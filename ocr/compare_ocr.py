"""
OCR 4종 성능 비교 스크립트 (최적화 버전)

핵심 개선:
- 카테고리별 파일 개수 제한 (기본 3개)
- Tesseract는 스캔 PDF만 실행
- 페이지 수 제한 (기본 3페이지)
"""

import sys
import time
import csv
import platform
from pathlib import Path
from datetime import datetime
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")  # ← 여기로 올려야 함 (import 직후)
import matplotlib.pyplot as plt

from pymupdf_ocr   import extract_text_pymupdf, is_scanned_pdf
from tesseract_ocr import extract_text_tesseract
from opencv_ocr    import extract_text_opencv

# 한글 폰트 설정
if platform.system() == "Darwin":
    plt.rcParams["font.family"] = "AppleGothic"
elif platform.system() == "Windows":
    plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False


BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"
RESULTS_DIR = BASE_DIR / "results"

# 🔥 설정값 (여기만 바꿔도 전체 조절됨)
LIMIT_PER_CATEGORY = 3   # 카테고리당 파일 개수
TESSERACT_PAGE_LIMIT = 3 # OCR 페이지 수 제한

METHODS = {
    "pymupdf"   : extract_text_pymupdf,
    "opencv"    : extract_text_opencv,
    "tesseract" : extract_text_tesseract,
}

# ── 진행상황 출력 ─────────────────────────────────────────
def log(msg: str):
    now = datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] {msg}", flush=True)


def print_progress(current: int, total: int, file_path: str):
    percent  = round(current / total * 100)
    bar_done = int(percent / 5)
    bar      = "█" * bar_done + "░" * (20 - bar_done)
    filename = Path(file_path).name
    print(f"\n  [{bar}] {percent}% ({current}/{total})")
    print(f"  현재 파일: {filename}", flush=True)


# ── 유틸 함수 ─────────────────────────────────────────────
def get_category(file_path: str) -> str:
    path = Path(file_path)
    if "data" in path.parts:
        idx = path.parts.index("data")
        if len(path.parts) > idx + 1:
            return path.parts[idx + 1]
    return path.parent.name


def collect_pdfs(target_path: str) -> list[str]:
    path = Path(target_path)
    if path.is_file() and path.suffix.lower() == ".pdf":
        return [str(path)]
    if path.is_dir():
        return [str(f) for f in path.rglob("*.pdf")]
    raise FileNotFoundError(f"경로가 존재하지 않습니다: {target_path}")


def collect_by_category(target_path: str) -> dict[str, list[str]]:
    files = collect_pdfs(target_path)
    result = {}

    for f in files:
        cat = get_category(f)
        result.setdefault(cat, []).append(f)

    # 🔥 카테고리별 샘플링
    for cat in result:
        result[cat] = result[cat][:LIMIT_PER_CATEGORY]

    return result


def save_output(text: str, file_path: str, method: str):
    category = get_category(file_path)
    filename = Path(file_path).stem

    save_dir = OUTPUT_DIR / method / category
    save_dir.mkdir(parents=True, exist_ok=True)

    save_path = save_dir / f"{filename}.txt"

    with open(save_path, "w", encoding="utf-8") as f:
        f.write(text)


def score_text(text: str) -> dict:
    if not text.strip():
        return {
            "글자수": 0,
            "한글비율": 0.0,
            "공백비율": 0.0,
            "특수문자비율": 0.0,
        }

    total = len(text)
    korean = sum(1 for c in text if "\uAC00" <= c <= "\uD7A3")
    spaces = text.count(" ") + text.count("\n")
    specials = sum(
        1 for c in text if not c.isalnum() and c not in " \n\t"
    )

    return {
        "글자수": total,
        "한글비율": round(korean / total * 100, 1),
        "공백비율": round(spaces / total * 100, 1),
        "특수문자비율": round(specials / total * 100, 1),
    }


# ── 핵심 비교 함수 ─────────────────────────────────────────
def compare_one_file(file_path: str, file_idx: int, file_total: int):
    rows = []

    print_progress(file_idx, file_total, file_path)

    scanned = is_scanned_pdf(file_path)

    for method_idx, (method, func) in enumerate(METHODS.items(), start=1):
        # 🔥 Tesseract는 스캔 PDF만 실행
        if method == "tesseract" and not scanned:
            log("  ⏭️ TESSERACT 스킵 (텍스트 PDF)")
            continue

        log(f"  {method_idx}/{len(METHODS)} {method.upper()} 실행 중...")

        start = time.time()

        try:
            # 🔥 페이지 제한 전달
            if method == "tesseract":
                text = func(file_path, page_limit=TESSERACT_PAGE_LIMIT)
            else:
                text = func(file_path)

            elapsed = round(time.time() - start, 2)
            metrics = score_text(text)

            save_output(text, file_path, method)

            log(f"  ✅ {method.upper()} 완료 ({elapsed}초 / {metrics['글자수']}자)")

            status = "성공"

        except Exception as e:
            elapsed = round(time.time() - start, 2)
            metrics = {"글자수": 0, "한글비율": 0.0, "공백비율": 0.0, "특수문자비율": 0.0}
            status = f"실패: {e}"
            text = ""
            log(f"  ❌ {method.upper()} 실패: {e}")

        rows.append({
            "파일명": Path(file_path).stem,
            "카테고리": get_category(file_path),
            "OCR방법": method,
            "상태": status,
            "처리시간(초)": elapsed,
            **metrics,
        })

    return rows

def plot_and_report(all_rows: list[dict]):
    """CSV 결과로 그래프 + 추천 리포트 자동 출력"""

    # 평균 계산
    summary = defaultdict(lambda: {
        "처리시간합": 0, "글자수합": 0, "한글비율합": 0,
        "특수문자합": 0, "count": 0
    })
    for row in all_rows:
        if "성공" not in row["상태"]:
            continue
        m = row["OCR방법"]
        summary[m]["처리시간합"] += row["처리시간(초)"]
        summary[m]["글자수합"]   += row["글자수"]
        summary[m]["한글비율합"] += row["한글비율"]
        summary[m]["특수문자합"] += row["특수문자비율"]
        summary[m]["count"]      += 1

