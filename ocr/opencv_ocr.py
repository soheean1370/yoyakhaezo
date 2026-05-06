import os
import sys
from pathlib import Path

import cv2
import fitz  # PyMuPDF
import numpy as np
import pytesseract
from PIL import Image


# Windows에서 Tesseract 설치 경로
# 본인 PC 설치 경로가 다르면 수정
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def pdf_to_images(pdf_path: str, image_dir: str, zoom: int = 2) -> list[str]:
    """
    PDF를 페이지별 PNG 이미지로 변환한다.
    OpenCV는 PDF를 직접 처리하지 못하므로 먼저 이미지로 변환한다.
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


def preprocess_image(image_path: str) -> np.ndarray:
    """
    OpenCV로 OCR 전처리를 수행한다.
    원본 이미지 → 그레이스케일 → 노이즈 제거 → 이진화
    """
    img = cv2.imread(image_path)

    if img is None:
        raise ValueError(f"이미지를 읽을 수 없습니다: {image_path}")

    # 1. 그레이스케일 변환
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 2. 노이즈 제거
    denoised = cv2.fastNlMeansDenoising(gray, h=5)

    # 3. Otsu 이진화
    _, binary = cv2.threshold(
        denoised,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    return binary


def extract_text_from_image_opencv(image_path: str, processed_save_path: str | None = None) -> str:
    """
    이미지 1장에 대해:
    OpenCV 전처리 → Tesseract OCR
    """
    processed = preprocess_image(image_path)

    # 전처리된 이미지 저장
    if processed_save_path is not None:
        os.makedirs(os.path.dirname(processed_save_path), exist_ok=True)
        cv2.imwrite(processed_save_path, processed)

    # OpenCV 결과는 numpy 배열이므로 PIL 이미지로 변환
    pil_image = Image.fromarray(processed)

    text = pytesseract.image_to_string(
        pil_image,
        lang="kor+eng",
        config="--psm 6"
    )

    return text


def extract_text_from_pdf_opencv(
    pdf_path: str,
    raw_image_root: str = "output/images/opencv/raw",
    processed_image_root: str = "output/images/opencv/processed",
    max_pages: int | None = 20 # 앞 20페이지만. None = None으로 바꾸면 전체
) -> str:
    """
    PDF 1개를 OpenCV 전처리 + Tesseract 방식으로 OCR한다.
    PDF → 이미지 변환 → OpenCV 전처리 → Tesseract OCR
    """
    pdf_name = Path(pdf_path).stem

    raw_image_dir = os.path.join(raw_image_root, pdf_name)
    processed_image_dir = os.path.join(processed_image_root, pdf_name)

    image_paths = pdf_to_images(pdf_path, raw_image_dir, zoom=2)

    if max_pages is not None:
        image_paths = image_paths[:max_pages]

    full_text = ""

    for index, image_path in enumerate(image_paths):
        page_num = index + 1
        print(f"  - {page_num}페이지 OpenCV 전처리 + Tesseract OCR 중...")

        processed_save_path = os.path.join(
            processed_image_dir,
            f"page_{page_num}_processed.png"
        )

        page_text = extract_text_from_image_opencv(
            image_path,
            processed_save_path=processed_save_path
        )

        full_text += f"\n\n===== PAGE {page_num} =====\n\n"
        full_text += page_text

    return full_text


def extract_text_opencv(file_path: str) -> str:
    """
    입력 파일이 PDF면 PDF 처리,
    이미지면 이미지 처리.
    """
    ext = Path(file_path).suffix.lower()

    if ext == ".pdf":
        return extract_text_from_pdf_opencv(file_path)

    elif ext in [".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"]:
        return extract_text_from_image_opencv(file_path)

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


def save_result(text: str, input_path: str, method: str = "opencv") -> str:
    """
    OCR 결과를 txt 파일로 저장한다.
    예:
    data/insurance/sample.pdf
    → output/opencv/insurance/sample.txt
    """
    category = get_category(input_path)
    filename = Path(input_path).stem

    save_dir = Path("output") / method / category
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
    python ocr/opencv_ocr.py data/insurance
    python ocr/opencv_ocr.py data/insurance/sample.pdf
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

    print(f"총 {len(files)}개 파일 OpenCV 전처리 + Tesseract OCR 시작")

    for index, file_path in enumerate(files, start=1):
        print("=" * 60)
        print(f"[{index}/{len(files)}] 실행 중: {file_path}")

        try:
            result = extract_text_opencv(file_path)
            saved_path = save_result(result, file_path, method="opencv")

            print(f"[저장 완료] {saved_path}")
            print(f"총 {len(result)}자 추출")
            print("미리보기:")
            print(result[:500])

        except Exception as e:
            print(f"[실패] {file_path}")
            print(f"오류 내용: {e}")

    print("=" * 60)
    print("전체 OpenCV 전처리 + Tesseract OCR 완료")


if __name__ == "__main__":
    main()