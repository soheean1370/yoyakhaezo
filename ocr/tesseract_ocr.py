import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from pathlib import Path
import io
import platform

if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def extract_text_tesseract(file_path: str, page_limit: int = 3):
    doc = fitz.open(file_path)

    text = ""

    for i in range(min(len(doc), page_limit)):
        print(f"  - {i+1}페이지 OCR 중...")

        page = doc[i]
        pix = page.get_pixmap()

        # 🔥 파일 저장 안 하고 바로 메모리에서 처리
        img_bytes = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_bytes))

        page_text = pytesseract.image_to_string(
            image,
            lang="kor+eng",
            config="--psm 6"
        )

        text += f"\n\n===== PAGE {i+1} =====\n\n"
        text += page_text

    doc.close()
    return text