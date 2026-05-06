import sys
from pathlib import Path

import fitz  # PyMuPDF


def is_scanned_pdf(file_path: str, min_chars_per_page: int = 30) -> bool:
    """
    PDF가 스캔 PDF인지 간단히 판단한다.

    기준:
    - 각 페이지에서 추출되는 텍스트 길이를 확인
    - 대부분의 페이지에서 텍스트가 거의 없으면 스캔 PDF로 판단

    주의:
    - 완벽한 판단은 아님
    - 표지나 이미지 많은 페이지는 텍스트가 적을 수 있음
    """
    doc = fitz.open(file_path)

    if len(doc) == 0:
        doc.close()
        return True

    text_pages = 0

    for page in doc:
        text = page.get_text().strip()

        if len(text) >= min_chars_per_page:
            text_pages += 1

    total_pages = len(doc)
    doc.close()

    # 텍스트가 있는 페이지가 전체의 20% 미만이면 스캔 PDF로 판단
    text_page_ratio = text_pages / total_pages

    return text_page_ratio < 0.2


def extract_text_pymupdf(file_path: str, max_pages: int | None = None) -> str:
    """
    PyMuPDF로 PDF 내부 텍스트를 직접 추출한다.
    OCR이 아니라 PDF에 저장된 텍스트 레이어를 읽는 방식이다.
    """
    doc = fitz.open(file_path)
    full_text = ""

    total_pages = len(doc)

    if max_pages is None:
        pages_to_read = total_pages
    else:
        pages_to_read = min(max_pages, total_pages)

    for page_index in range(pages_to_read):
        page = doc[page_index]

        text = page.get_text("text")

        full_text += f"\n\n===== PAGE {page_index + 1} =====\n\n"
        full_text += text

    doc.close()

    return full_text


def extract_text_pymupdf_blocks(file_path: str, max_pages: int | None = None) -> str:
    """
    block 단위로 텍스트를 추출한다.
    일반 get_text("text") 결과가 너무 섞이면 이 방식도 비교해볼 수 있다.

    block 방식은 좌표 기반으로 텍스트 블록을 가져와서
    위에서 아래 순서로 정렬한 뒤 합친다.
    """
    doc = fitz.open(file_path)
    full_text = ""

    total_pages = len(doc)

    if max_pages is None:
        pages_to_read = total_pages
    else:
        pages_to_read = min(max_pages, total_pages)

    for page_index in range(pages_to_read):
        page = doc[page_index]

        blocks = page.get_text("blocks")

        # blocks 각 항목 구조:
        # (x0, y0, x1, y1, text, block_no, block_type)
        blocks = sorted(blocks, key=lambda b: (b[1], b[0]))

        full_text += f"\n\n===== PAGE {page_index + 1} =====\n\n"

        for block in blocks:
            block_text = block[4].strip()

            if block_text:
                full_text += block_text + "\n"

    doc.close()

    return full_text


def get_category(input_path: str) -> str:
    """
    data/card/파일.pdf      → card
    data/deposit/파일.pdf   → deposit
    data/insurance/파일.pdf → insurance
    """
    path = Path(input_path)

    if "data" in path.parts:
        data_index = path.parts.index("data")

        if len(path.parts) > data_index + 1:
            return path.parts[data_index + 1]

    return path.parent.name


def save_result(text: str, input_path: str, method: str = "pymupdf") -> str:
    """
    추출 결과를 txt 파일로 저장한다.

    예:
    data/insurance/sample.pdf
    → output/pymupdf/insurance/sample.txt
    """
    category = get_category(input_path)
    filename = Path(input_path).stem

    save_dir = Path("output") / method / category
    save_dir.mkdir(parents=True, exist_ok=True)

    save_path = save_dir / f"{filename}.txt"

    with open(save_path, "w", encoding="utf-8") as f:
        f.write(text)

    return str(save_path)


def save_skipped_file(input_path: str, reason: str, method: str = "pymupdf") -> str:
    """
    스캔 PDF라서 PyMuPDF 직접 추출을 건너뛴 파일을 기록한다.
    """
    category = get_category(input_path)
    filename = Path(input_path).stem

    save_dir = Path("output") / method / category / "_skipped"
    save_dir.mkdir(parents=True, exist_ok=True)

    save_path = save_dir / f"{filename}_skipped.txt"

    with open(save_path, "w", encoding="utf-8") as f:
        f.write(f"파일: {input_path}\n")
        f.write(f"사유: {reason}\n")

    return str(save_path)


def collect_files(target_path: str) -> list[str]:
    """
    입력이 파일이면 파일 1개 반환.
    입력이 폴더면 내부 PDF 파일 전체 반환.
    """
    path = Path(target_path)

    if path.is_file():
        if path.suffix.lower() == ".pdf":
            return [str(path)]
        else:
            raise ValueError(f"PyMuPDF 직접 추출은 PDF만 지원합니다: {path.suffix}")

    if path.is_dir():
        pdf_files = list(path.rglob("*.pdf"))
        return [str(file) for file in pdf_files]

    raise FileNotFoundError(f"파일 또는 폴더가 존재하지 않습니다: {target_path}")


def main():
    """
    사용 예시:
    python ocr/pymupdf_ocr.py data/insurance
    python ocr/pymupdf_ocr.py data/insurance/sample.pdf
    """
    target_path = sys.argv[1] if len(sys.argv) > 1 else "data/insurance"

    try:
        files = collect_files(target_path)
    except Exception as e:
        print(f"[오류] {e}")
        sys.exit(1)

    if not files:
        print(f"PDF 파일이 없습니다: {target_path}")
        sys.exit(0)

    print(f"총 {len(files)}개 PDF PyMuPDF 직접 추출 시작")

    for index, file_path in enumerate(files, start=1):
        print("=" * 60)
        print(f"[{index}/{len(files)}] PyMuPDF 처리 중: {file_path}")

        try:
            if is_scanned_pdf(file_path):
                print("⚠️  스캔 PDF로 판단됨 → PyMuPDF 직접 추출 건너뜀")
                skipped_path = save_skipped_file(
                    file_path,
                    reason="텍스트 레이어가 거의 없어 OCR 필요"
                )
                print(f"[스킵 기록 저장] {skipped_path}")
                continue

            # 테스트용으로 앞 20페이지만 추출
            # 전체 페이지를 하려면 max_pages=None으로 변경
            result = extract_text_pymupdf(file_path, max_pages=20)

            saved_path = save_result(result, file_path, method="pymupdf")

            print(f"[저장 완료] {saved_path}")
            print(f"총 {len(result)}자 추출")
            print("미리보기:")
            print(result[:500])

        except Exception as e:
            print(f"[실패] {file_path}")
            print(f"오류 내용: {e}")

    print("=" * 60)
    print("전체 PyMuPDF 직접 추출 완료")


if __name__ == "__main__":
    main()