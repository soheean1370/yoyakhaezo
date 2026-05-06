import os
import sys
from pathlib import Path

import fitz
import easyocr


def pdf_to_images(pdf_path: str, image_dir: str, zoom: int = 2) -> list[str]:
    """
    PDF를 페이지별 PNG 이미지로 변환한다.
    easyOCR은 이미지 OCR 도구이므로 PDF를 먼저 이미지로 바꾼다.
    """
    os.makedirs(image_dir, exist_ok=True)

    doc = fitz.open(pdf_path)
    image_paths = []

    for page_index in range(len(doc)):
        page = doc[page_index]

        matrix = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix)

        image_path = os.path.join(image_dir, f"page_{page_index + 1}.png")
        pix.save(image_path)

        image_paths.append(image_path)

    doc.close()
    return image_paths


def create_easyocr_reader() -> easyocr.Reader:
    """
    easyOCR Reader를 생성한다.
    처음 실행할 때 모델 파일을 다운로드할 수 있다.
    """
    reader = easyocr.Reader(
        ["ko", "en"],
        gpu=False
    )
    return reader


def extract_text_from_image_easyocr(reader: easyocr.Reader, image_path: str) -> str:
    """
    이미지 1장에 대해 easyOCR을 실행한다.
    """
    result = reader.readtext(
        image_path,
        detail=0,
        paragraph=False
    )

    text = "\n".join(result)
    return text


def extract_text_from_pdf_easyocr(
    reader: easyocr.Reader,
    pdf_path: str,
    temp_image_root: str = "output/images/easyocr",
    max_pages: int | None = 20
) -> str:
    """
    PDF 1개를 easyOCR로 OCR한다.
    PDF → 이미지 변환 → 페이지별 OCR → 텍스트 합치기
    """
    pdf_name = Path(pdf_path).stem

    image_dir = os.path.join(temp_image_root, pdf_name)
    image_paths = pdf_to_images(pdf_path, image_dir, zoom=2)

    if max_pages is not None:
        image_paths = image_paths[:max_pages]

    full_text = ""

    for index, image_path in enumerate(image_paths):
        print(f"  - {index + 1}페이지 easyOCR 실행 중...")

        page_text = extract_text_from_image_easyocr(reader, image_path)

        full_text += f"\n\n===== PAGE {index + 1} =====\n\n"
        full_text += page_text

    return full_text


def extract_text_easyocr(reader: easyocr.Reader, file_path: str) -> str:
    """
    입력 파일이 PDF면 PDF OCR,
    이미지면 이미지 OCR을 수행한다.
    """
    ext = Path(file_path).suffix.lower()

    if ext == ".pdf":
        return extract_text_from_pdf_easyocr(reader, file_path)

    elif ext in [".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"]:
        return extract_text_from_image_easyocr(reader, file_path)

    else:
        raise ValueError(f"지원하지 않는 파일 형식입니다: {ext}")


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


def save_result(text: str, input_path: str, method: str = "easyocr") -> str:
    """
    OCR 결과를 txt 파일로 저장한다.
    예:
    data/insurance/sample.pdf
    → data/output/easyocr/insurance/sample.txt
    """
    category = get_category(input_path)
    filename = Path(input_path).stem

    save_dir = Path("data/output") / method / category
    save_dir.mkdir(parents=True, exist_ok=True)

    save_path = save_dir / f"{filename}.txt"

    with open(save_path, "w", encoding="utf-8") as f:
        f.write(text)

    return str(save_path)


def collect_files(target_path: str) -> list[str]:
    """
    입력이 파일이면 파일 1개 반환.
    입력이 폴더면 내부 PDF/이미지 파일 전체 반환.
    """
    path = Path(target_path)

    supported_exts = [".pdf", ".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"]

    if path.is_file():
        if path.suffix.lower() in supported_exts:
            return [str(path)]
        else:
            raise ValueError(f"지원하지 않는 파일 형식입니다: {path.suffix}")

    if path.is_dir():
        files = []

        for ext in supported_exts:
            files.extend(path.rglob(f"*{ext}"))

        return [str(file) for file in files]

    raise FileNotFoundError(f"파일 또는 폴더가 존재하지 않습니다: {target_path}")


def main():
    """
    사용 예시:
    python ocr/easyocr_ocr.py data/insurance
    python ocr/easyocr_ocr.py data/insurance/sample.pdf
    """
    target_path = sys.argv[1] if len(sys.argv) > 1 else "data/insurance"

    if not os.path.exists(target_path):
        print(f"파일 또는 폴더 없음: {target_path}")
        sys.exit(1)

    try:
        files = collect_files(target_path)
    except Exception as e:
        print(f"[오류] {e}")
        sys.exit(1)

    if not files:
        print(f"OCR 대상 파일이 없습니다: {target_path}")
        sys.exit(0)

    print("easyOCR Reader 준비 중...")
    reader = create_easyocr_reader()

    print(f"총 {len(files)}개 파일 easyOCR 시작")

    for index, file_path in enumerate(files, start=1):
        print("=" * 60)
        print(f"[{index}/{len(files)}] easyOCR 실행 중: {file_path}")

        try:
            result = extract_text_easyocr(reader, file_path)
            saved_path = save_result(result, file_path, method="easyocr")

            print(f"[저장 완료] {saved_path}")
            print(f"총 {len(result)}자 추출")
            print("미리보기:")
            print(result[:500])

        except Exception as e:
            print(f"[실패] {file_path}")
            print(f"오류 내용: {e}")

    print("=" * 60)
    print("전체 easyOCR 완료")


if __name__ == "__main__":
    main()