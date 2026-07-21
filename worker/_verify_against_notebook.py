"""worker/_verify_against_notebook.py — predict() 이식 정확성 '숫자' 검증 (로컬 전용, 커밋 안 함).

dict 모양만 보는 스모크 테스트는 전처리가 틀려도 통과한다(= 조용한 Recall 하락).
그래서 노트북 v7 이 캐시한 정답 앙상블 확률과 predict() 출력을 직접 대조한다.

정답지(레포 밖, 원본 경로에서 읽음 — worker/models 로 복사 금지: Kaggle test셋):
  <원본>/ckpt_v7/v7_probs.npz  키 "test_ms" (624,)  = 3-scale × 5-fold 평균 = predict 와 동일 계산
  <원본>/data/test.csv         file_name 컬럼, test_0001~0624 순서
  <원본>/data/test/*.png       그 이미지들
※ 오라클은 반드시 "test_ms". "ens_test" 는 rate/앙상블 보정이 더 붙어 predict 와 안 맞음.

판정(둘 다 충족해야 PASS):
  - 확률 MAE(10장 평균 절대오차) < 0.05
  - is_pneumonia 결정(>=0.5) 이 정답과 10/10 일치
    (단 p_true 가 0.45~0.55 경계인 장은 결정 일치 집계에서 제외하고 로그)
"""

import csv
import os
import sys
import time

import numpy as np

# 이 스크립트를 `python worker/_verify_against_notebook.py` 로 직접 실행해도
# `from worker.model import predict` 가 되도록 레포 루트를 sys.path 에 추가.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from worker.model import MODEL_TAG, predict  # noqa: E402

# ★ 각자 v7 노트북 데이터/ckpt 경로로 바꾸세요 (레포 밖, 커밋 안 되는 Kaggle test셋).
#   이 폴더 아래에 ckpt_v7/v7_probs.npz, data/test.csv, data/test/*.png 이 있어야 함.
NOTEBOOK_DATA_DIR = "/Users/gwonbyeonghag/Desktop/02_개발/01_개발 공부/01_A_ health_chare_5/99_프로젝트/03_흉부 X-ray"

PROBS_NPZ = os.path.join(NOTEBOOK_DATA_DIR, "ckpt_v7", "v7_probs.npz")
TEST_CSV = os.path.join(NOTEBOOK_DATA_DIR, "data", "test.csv")
TEST_DIR = os.path.join(NOTEBOOK_DATA_DIR, "data", "test")

N = 10                 # 대조 장수
MAE_THRESHOLD = 0.05   # 확률 MAE 허용치(CPU↔GPU·버전차 미세오차 감안)
BOUNDARY = (0.45, 0.55)  # 이 구간 p_true 는 결정 일치 집계에서 제외(경계라 뒤집히기 쉬움)


def main():
    test_ms = np.load(PROBS_NPZ)["test_ms"]  # (624,) 정답 앙상블 확률
    with open(TEST_CSV, newline="") as f:    # file_name, test_0001~ 순서 (test_ms 와 동일 정렬)
        file_names = [row["file_name"] for row in csv.DictReader(f)]

    rows = []
    abs_diffs = []
    decided = 0          # 결정 일치 집계 대상(경계 제외) 장수
    decided_match = 0    # 그중 결정 일치 장수

    for i in range(N):
        fname = file_names[i]
        p_true = float(test_ms[i])
        img_path = os.path.join(TEST_DIR, fname)

        r = predict(img_path)
        p_hat = r["confidence"] / 100.0

        diff = abs(p_hat - p_true)
        abs_diffs.append(diff)

        is_boundary = BOUNDARY[0] <= p_true <= BOUNDARY[1]
        dec_true = p_true >= 0.5
        dec_hat = r["is_pneumonia"]
        if is_boundary:
            match_str = "제외(경계)"
        else:
            decided += 1
            if dec_true == dec_hat:
                decided_match += 1
                match_str = "O"
            else:
                match_str = "X"

        rows.append((fname, p_true, p_hat, diff, match_str))

    mae = float(np.mean(abs_diffs))

    # ---- 결과표 ----
    print("=" * 72)
    print(f"predict() vs 노트북 v7 test_ms 대조 (앞 {N}장)   ai_model={MODEL_TAG}")
    print("=" * 72)
    print(f"{'file_name':<16}{'p_true':>10}{'p_hat':>10}{'|diff|':>10}{'결정일치':>12}")
    print("-" * 72)
    for fname, p_true, p_hat, diff, match_str in rows:
        print(f"{fname:<16}{p_true:>10.4f}{p_hat:>10.4f}{diff:>10.4f}{match_str:>12}")
    print("-" * 72)
    print(f"확률 MAE(10장 평균 절대오차) = {mae:.4f}   (허용 < {MAE_THRESHOLD})")
    print(f"결정 일치 = {decided_match}/{decided}"
          + (f"  (경계 {N - decided}장 제외)" if decided < N else ""))

    mae_ok = mae < MAE_THRESHOLD
    dec_ok = (decided_match == decided) and decided > 0
    passed = mae_ok and dec_ok

    print("-" * 72)
    print(f"MAE 판정      : {'PASS' if mae_ok else 'FAIL'}")
    print(f"결정 일치 판정: {'PASS' if dec_ok else 'FAIL'}")
    print(f"==> 최종: {'PASS ✅' if passed else 'FAIL ❌'}")
    print("=" * 72)

    if not passed:
        print(
            "\n⚠️ FAIL: 이식이 틀렸을 수 있음. MAE 가 0.2+ 거나 결정이 여러 장 뒤집히면\n"
            "   어느 단계가 의심되는지 점검: 표준화(nyul_map/S_REF) / CLAHE(2.0,8x8) /\n"
            "   스케일(224,256,288) / fold state_dict 로드."
        )
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    _t0 = time.time()
    try:
        main()
    finally:
        print(f"(검증 총 소요: {round(time.time() - _t0, 2)}초, {N}장 × 15추론)")
