import cv2
import pytesseract
import numpy as np
from PIL import Image
import sys
import os

def preprocess_image(image_path: str) -> np.ndarray:
    img = cv2.imread(image_path)

    # 그레이스케일 변환
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 노이즈 제거
    denoised = cv2.fastNlMeansDenoising(gray, h=10)

    # 이진화
    _, binary = cv2.threshold(
        denoised, 0, 255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    return binary

def extract_text_opencv(file_path: str) -> str:
    processed = preprocess_image(file_path)

    temp_path = "temp_processed.png"
    cv2.imwrite(temp_path, processed)

    image = Image.open(temp_path)
    text  = pytesseract.image_to_string(image, lang="kor+eng")

    os.remove(temp_path)
    return text

def save_result(text: str, input_path: str, method: str = "opencv"):
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

    print(f"OpenCV 전처리 + Tesseract 실행 중: {test_file}")
    result = extract_text_opencv(test_file)

    saved = save_result(result, test_file, method="opencv")

    print("=" * 50)
    print(f"[저장 완료] {saved}")
    print("=" * 50)
    print(result[:500])
    print(f"\n총 {len(result)}자 추출")