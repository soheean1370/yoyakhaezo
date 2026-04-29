import fitz  # PyMuPDF
import sys
import os

def is_scanned_pdf(file_path: str) -> bool:
    doc  = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return len(text.strip()) < 100

def extract_text_pymupdf(file_path: str) -> str:
    doc       = fitz.open(file_path)
    full_text = ""
    for page_num, page in enumerate(doc):
        text       = page.get_text()
        full_text += f"\n--- {page_num + 1}페이지 ---\n"
        full_text += text
    doc.close()
    return full_text

def save_result(text: str, input_path: str, method: str = "pymupdf"):
    category = os.path.dirname(input_path).split("/")[-1]
    filename  = os.path.splitext(os.path.basename(input_path))[0]
    save_dir  = f"output/{method}/{category}"
    os.makedirs(save_dir, exist_ok=True)
    save_path = f"{save_dir}/{filename}.txt"
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(text)
    return save_path

if __name__ == "__main__":
    test_file = sys.argv[1] if len(sys.argv) > 1 else "data/card/test.pdf"

    if not os.path.exists(test_file):
        print(f"파일 없음: {test_file}")
        sys.exit(1)

    # 스캔 PDF 여부 먼저 확인
    if is_scanned_pdf(test_file):
        print("⚠️  스캔 PDF 감지 → OCR 사용 필요 (tesseract 또는 easyocr 권장)")
        sys.exit(0)

    print(f"PyMuPDF 직접 추출 중: {test_file}")
    result = extract_text_pymupdf(test_file)

    saved = save_result(result, test_file, method="pymupdf")

    print("=" * 50)
    print(f"[저장 완료] {saved}")
    print("=" * 50)
    print(result[:500])
    print(f"\n총 {len(result)}자 추출")