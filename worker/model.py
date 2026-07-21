"""worker/model.py — v7 흉부 X-ray 폐렴 예측 모델 (densenet121 5-fold 앙상블) 이식.

해커톤 v7 노트북(chest_xray_v7_mission7.ipynb)의 '추론 경로'만 서버용으로 이식했다.
학습 코드는 전부 제외하고, 전처리 → 멀티스케일 TTA → 5-fold 앙상블 → predict() 만 담는다.

노트북(Kaggle 제출용) 대비 3가지만 바꿈:
  - 입력: pandas DataFrame(배치)  → 이미지 파일 경로 1장
  - 출력: 제출 CSV               → dict 1개
  - 디바이스: GPU/autocast 전제   → CPU(fp32). autocast/GradScaler/cuda 코드 전부 제거.

⚠️ 전처리 파라미터는 학습과 100% 동일해야 성능(Recall)이 유지된다.
   순서: Nyúl 히스토그램 표준화 → CLAHE(2.0, 8x8) → 3채널 → [224,256,288] 멀티스케일.
   이 순서/파라미터를 하나라도 바꾸면 학습과 입력 분포가 달라져 Recall 이 조용히 떨어진다.
"""

from __future__ import annotations

import os

import albumentations as A
import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from albumentations.pytorch import ToTensorV2
from PIL import Image
from torchvision import models

# ---------------------------------------------------------------------------
# (a) 상수 — 노트북 값 그대로. 하나라도 틀리면 학습과 입력이 달라진다.
# ---------------------------------------------------------------------------
BACKBONE = "densenet121"
SCALES = (224, 256, 288)                       # 멀티스케일 TTA
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]
LANDMARK_PCTS = [1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 99]
MODEL_TAG = "v7_densenet121_5fold"             # ai_model 필드로 응답·저장됨
FOLDS = 5

_MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
_REF_PATH = os.path.join(_MODELS_DIR, "hist_ref.npz")

# CLAHE: 노트북과 동일 파라미터 (표준화 後 적용)
CLAHE_OP = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

# 표준 landmark S: train 기준 히스토그램(hist_ref.npz["S"]). 프로세스당 1회 로드(672B, 경량).
_ref = np.load(_REF_PATH)
S_REF = _ref["S"]
assert list(_ref["pcts"]) == LANDMARK_PCTS, (
    f"landmark 분위수 불일치: {list(_ref['pcts'])} != {LANDMARK_PCTS}"
)


# ---------------------------------------------------------------------------
# (c) 전처리 — 노트북 함수 그대로 이식 (_landmarks, _strict_inc, nyul_map,
#     load_std_clahe_3ch). 순서: 히스토그램 표준화 → CLAHE → 3채널.
# ---------------------------------------------------------------------------
def _landmarks(gray):
    return np.percentile(gray.astype(np.float32), LANDMARK_PCTS)


def _strict_inc(a, eps=1e-3):
    a = np.maximum.accumulate(np.asarray(a, dtype=np.float32))
    for i in range(1, len(a)):
        if a[i] <= a[i - 1]:
            a[i] = a[i - 1] + eps
    return a


def nyul_map(gray, S):
    """이미지 landmark L → 표준 스케일 S 로 piecewise-linear 매핑 (train 기준 S 고정)."""
    L = _strict_inc(_landmarks(gray))
    Sx = _strict_inc(S)
    out = np.interp(gray.astype(np.float32).ravel(), L, Sx)  # 범위 밖은 S 양끝으로 clamp
    return np.clip(out, 0, 255).reshape(gray.shape).astype(np.uint8)


def load_std_clahe_3ch(path):
    gray = np.array(Image.open(path).convert("L"))
    std = nyul_map(gray, S_REF)          # 1) 히스토그램 표준화(train 기준 S_REF)
    g = CLAHE_OP.apply(std)              # 2) CLAHE (표준화 後)
    return np.stack([g, g, g], axis=-1)  # 3) 3채널 (resize/norm은 transform에서)


def _eval_tf(s):
    """노트북 eval_tf_scale(s): squish Resize → ImageNet 정규화 → 텐서."""
    return A.Compose([
        A.Resize(s, s),
        A.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ToTensorV2(),
    ])


# ---------------------------------------------------------------------------
# (b) 아키텍처 — 노트북 build_backbone 그대로. 서버는 사전학습 weight 없이
#     state_dict 로 채우므로 weights=None.
# ---------------------------------------------------------------------------
def build_backbone(name=BACKBONE):
    if name == "densenet121":
        m = models.densenet121(weights=None)
        m.classifier = nn.Linear(m.classifier.in_features, 2)
    else:
        raise ValueError(f"unknown backbone {name}")
    return m


# ---------------------------------------------------------------------------
# (d) 모델 로드 — 프로세스당 1회, lazy. 앱 import 시점에 로드하지 않는다
#     (테스트·다른 API 기동 지연 방지). 최초 predict() 호출 때 1회만.
# ---------------------------------------------------------------------------
_FOLD_MODELS = None


def load_models():
    """fold0~4.pth 를 build_backbone 에 load_state_dict → eval() → CPU. 전역 캐시(1회)."""
    global _FOLD_MODELS
    if _FOLD_MODELS is not None:
        return _FOLD_MODELS
    loaded = []
    for k in range(FOLDS):
        path = os.path.join(_MODELS_DIR, f"fold{k}.pth")
        state = torch.load(path, map_location="cpu")   # CPU 강제(서버 환경)
        m = build_backbone(BACKBONE)
        m.load_state_dict(state)
        m.eval()
        loaded.append(m)
    _FOLD_MODELS = loaded
    return _FOLD_MODELS


# ---------------------------------------------------------------------------
# (e) 핵심 함수 — 산출물의 계약. 노트북 predict_ms 를 이미지 1장용으로 축약.
# ---------------------------------------------------------------------------
@torch.no_grad()
def predict(image_path: str) -> dict:
    """X-ray 1장 → 폐렴 예측.

    전처리(표준화→CLAHE→3채널) 후 3 scale × 5 fold = 15회 softmax 확률을 평균해
    폐렴(class 1) 확률을 낸다. 노트북 test_ms(3-scale × 5-fold 평균)와 동일한 계산.
    전부 torch.no_grad() 안에서 동작하고, autocast/GradScaler/cuda 는 쓰지 않는다(CPU).
    """
    fold_models = load_models()
    img = load_std_clahe_3ch(image_path)   # HxWx3 uint8 (표준화+CLAHE)

    probs = []
    for s in SCALES:
        x = _eval_tf(s)(image=img)["image"].unsqueeze(0)   # 1x3xsxs, fp32
        for m in fold_models:
            p = F.softmax(m(x), dim=1)[:, 1]               # 폐렴=class 1 확률
            probs.append(float(p.item()))
    prob = float(np.mean(probs))                           # 15개 평균

    return {
        "is_pneumonia": bool(prob >= 0.5),
        # confidence 는 '폐렴일 확률'(0~100). is_pneumonia=False 여도 그 확률(0.5 미만) 그대로.
        # 팀이 '예측한 클래스의 확신도'를 원하면 아래 한 줄로 교체:
        #     conf = max(prob, 1.0 - prob)  →  round(conf * 100, 2)
        "confidence": round(prob * 100, 2),                # DB Numeric(5,2) 정합
        "ai_model": MODEL_TAG,
    }
