import pytesseract
from PIL import Image
import sys
import os

def extract_text_tesseract(file_path: str) -> str:
    image = Image.open(file_path)
    text = pytesseract.image_to_string(image, lang="kor+eng")
    return text

def save_result(text: str, input_path: str, method: str = "tesseract"):
    category = os.path.dirname(input_path).split("/")[-1]
    filename  = os.path.splitext(os.path.basename(input_path))[0]
    save_dir  = f"output/{method}/{category}"
    os.makedirs(save_dir, exist_ok=True)
    save_path = f"{save_dir}/{filename}.txt"
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(text)
    return save_path

if __name__ == "__main__":
    test_file = sys.argv[1] if len(sys.argv) > 1 else "data/card/test.png"

    if not os.path.exists(test_file):
        print(f"파일 없음: {test_file}")
        sys.exit(1)

    print(f"Tesseract OCR 실행 중: {test_file}")
    result = extract_text_tesseract(test_file)

    saved = save_result(result, test_file, method="tesseract")

    print("=" * 50)
    print(f"[저장 완료] {saved}")
    print("=" * 50)
    print(result[:500])
    print(f"\n총 {len(result)}자 추출")