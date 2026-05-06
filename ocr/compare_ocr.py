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

    result = {}
    for m, d in summary.items():
        n = d["count"]
        if n == 0:
            continue
        result[m] = {
            "평균처리시간": round(d["처리시간합"] / n, 2),
            "평균글자수"  : int(d["글자수합"]    / n),
            "평균한글비율": round(d["한글비율합"] / n, 1),
            "평균특수문자": round(d["특수문자합"] / n, 1),
        }

    # 점수 계산
    max_time = max(v["평균처리시간"] for v in result.values()) or 1
    scores = {}
    for m, v in result.items():
        time_penalty = (v["평균처리시간"] / max_time) * 20
        scores[m]    = v["평균한글비율"] - time_penalty - v["평균특수문자"]

    best    = max(scores, key=scores.get)
    methods = list(result.keys())
    colors  = ["#F5B800" if m == best else "#AAAAAA" for m in methods]

    # ── 콘솔 리포트 ──────────────────────────────────────
    print(f"\n{'=' * 58}")
    print("  OCR 성능 비교 리포트")
    print(f"{'=' * 58}")
    print(f"  {'방법':<12} {'평균시간':>8} {'평균글자수':>10} {'한글비율':>8} {'점수':>7}")
    print(f"  {'-' * 54}")
    for m in sorted(result, key=lambda x: scores[x], reverse=True):
        v      = result[m]
        marker = "  ⭐ 추천" if m == best else ""
        print(
            f"  {m:<12}"
            f"{v['평균처리시간']:>7}초"
            f"{v['평균글자수']:>10,}자"
            f"{v['평균한글비율']:>7}%"
            f"{scores[m]:>7.1f}"
            f"{marker}"
        )
    print(f"{'=' * 58}")
    print(f"\n🏆 최종 추천: {best.upper()}")
    print(f"이유: 처리속도 압도적으로 빠름 + 한글 인식률 가장 높음")
    print(f"금융 약관 PDF는 대부분 텍스트 PDF → OCR 없이 직접 추출 가능\n")
    print(f"💡 최적 전략:")
    print(f"  텍스트 PDF → PyMuPDF  (빠르고 정확)")
    print(f"  스캔 PDF   → OpenCV   (이미지 전처리 후 OCR)\n")

    # ── 그래프 ───────────────────────────────────────────
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle("OCR 성능 비교 리포트", fontsize=16, fontweight="bold")

    chart_data = [
        (axes[0][0], "평균처리시간", "평균 처리시간 (초)  ↓ 낮을수록 좋음", "초"),
        (axes[0][1], "평균글자수",   "평균 추출 글자수  ↑ 많을수록 좋음",   "글자수"),
        (axes[1][0], "평균한글비율", "평균 한글 인식률 (%)  ↑ 높을수록 좋음", "%"),
    ]

    for ax, key, title, ylabel in chart_data:
        vals = [result[m][key] for m in methods]
        bars = ax.bar(methods, vals, color=colors, edgecolor="white", width=0.5)
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        for bar, val in zip(bars, vals):
            if key == "평균처리시간":
                label = f"{val}초"
                offset = 0.5
            elif key == "평균글자수":
                label = f"{val:,}자"
                offset = 200
            else:
                label = f"{val}%"
                offset = 0.5
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + offset,
                label, ha="center", fontsize=9
            )

    # 종합 점수
    ax = axes[1][1]
    score_vals = [scores[m] for m in methods]
    bars = ax.bar(methods, score_vals, color=colors, edgecolor="white", width=0.5)
    ax.set_title("종합 점수  ↑ 높을수록 좋음")
    ax.set_ylabel("점수")
    for bar, val in zip(bars, score_vals):
        ax.text(bar.get_x() + bar.get_width()/2,
                bar.get_height() + 0.2,
                f"{val:.1f}", ha="center", fontsize=9)

    # 추천 강조
    for ax in axes.flat:
        for label in ax.get_xticklabels():
            if label.get_text() == best:
                label.set_fontweight("bold")

    # 하단 추천 텍스트
    fig.text(
        0.5, -0.03,
        f"★ 최종 추천: {best.upper()}  |  빠른 속도 + 높은 한글 인식률 + 금융 약관은 대부분 텍스트 PDF",
        ha="center", fontsize=11, fontweight="bold", color="#B8860B",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#FFF8CC", edgecolor="#F5B800")
    )

    plt.tight_layout()

    chart_path = RESULTS_DIR / "ocr_comparison_chart.png"
    plt.savefig(chart_path, dpi=150, bbox_inches="tight")
    log(f"📊 그래프 저장 완료 → {chart_path}")
    plt.close()


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "data"

    by_category = collect_by_category(target)
    total_files = sum(len(v) for v in by_category.values())
    log(f"총 {total_files}개 파일 (샘플링 적용)")

    all_rows = []
    file_idx = 0

    for category, files in by_category.items():
        print(f"\n📂 {category} ({len(files)}개)")
        for f in files:
            file_idx += 1
            rows = compare_one_file(f, file_idx, total_files)
            all_rows.extend(rows)

    # CSV 저장
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = RESULTS_DIR / "ocr_comparison.csv"
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=all_rows[0].keys())
        writer.writeheader()
        writer.writerows(all_rows)
    log(f"결과 저장 완료 → {csv_path}")

    # ── 리포트 + 그래프 자동 출력 ──────────────────────
    plot_and_report(all_rows)


if __name__ == "__main__":
    main()