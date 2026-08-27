# 요약해조 🐟
> NLP 기반 금융 문서 이해 지원 서비스


https://yoyakhaezo.streamlit.app

---

## 시작하기

### 1. 레포지토리 클론
```bash
git clone https://github.com/your-repo/요약해조.git
cd 요약해조
```

### 2. 가상환경 만들기

**Mac / Linux**
```bash
python3 -m venv .venv
```

**Windows**
```bash
python -m venv .venv
```

### 3. 가상환경 활성화

**Mac / Linux**
```bash
source .venv/bin/activate
```

**Windows**
```bash
venv\Scripts\activate
```
### 4. 라이브러리 설치
```bash
pip install -r requirements.txt
```

### 5. Tesseract 설치 (별도 설치 필요)

**Mac**
```bash
brew install tesseract
brew install tesseract-lang
```

**Windows**
- https://github.com/UB-Mannheim/tesseract/wiki 에서 설치파일 다운로드
- 설치 시 "Additional language data" 에서 Korean 체크

### 6. 가상환경 비활성화 (작업 끝났을 때)
```bash
deactivate
```

---

## 자주 쓰는 명령어

```bash
# 가상환경 활성화 (작업 시작할 때마다)
source venv/bin/activate       # Mac
venv\Scripts\activate          # Windows

# 패키지 새로 설치했을 때 requirements 업데이트
pip freeze > requirements.txt

# Streamlit 실행
streamlit run app.py

# OCR 테스트 실행
python ocr/pymupdf_ocr.py data/card/test.pdf
python ocr/tesseract_ocr.py data/card/test.png
python ocr/opencv_ocr.py data/card/test.png
python ocr/easyocr_ocr.py data/card/test.png
```

---

## 주의사항

- `.venv/` 폴더는 깃헙에 올리지 않아요 (`.gitignore` 에 포함됨)
- PDF 파일은 용량 문제로 깃헙에 올리지 않아요
- 팀원이 새로 클론했을 때 **반드시 2~4번 과정** 다시 진행해야 해요

---

## 프로젝트 구조
```
요약해조/
├── data/
│   ├── card/           # 카드 약관 PDF
│   ├── insurance/      # 보험 약관 PDF
│   └── savings/        # 예적금 약관 PDF
├── ocr/
│   ├── tesseract_ocr.py
│   ├── opencv_ocr.py
│   ├── pymupdf_ocr.py
│   └── easyocr_ocr.py
├── output/             # 추출 결과 텍스트 저장
│   ├── tesseract/
│   ├── opencv/
│   ├── pymupdf/
│   └── easyocr/
├── preprocessing/
├── app.py
├── requirements.txt
├── .gitignore
└── README.md
```
