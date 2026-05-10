"""
정제된 금융/보험/카드/예금 텍스트를 chunk 단위로 분리하는 코드

입력:
- preprocessing/cleaned/card/*_cleaned.txt
- preprocessing/cleaned/deposit/*_cleaned.txt
- preprocessing/cleaned/insurance/*_cleaned.txt

출력:
- preprocessing/results/{category}/*_chunks.txt

특징:
- kss 설치 여부 확인 후 사용
- 제목, 조항, 항목, Q&A, 표 항목은 최대한 보존
- 특정 상품명보다 제목/번호/표 형태 중심으로 chunk 분리
- 카드 혜택표 / 해외 이용 수수료표 분리 보강
- 실손보험 표성 문장 분리 보강
- 터미널 출력: 파일명 -> 청크 수
"""

import re
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", category=UserWarning)


# =========================================================
# Optional Library Import
# =========================================================

USE_KSS = True

try:
    import kss

    KSS_AVAILABLE = True
    KSS_ERROR = ""
except ImportError:
    kss = None
    KSS_AVAILABLE = False
    KSS_ERROR = "kss 모듈이 설치되어 있지 않습니다."
except Exception as e:
    kss = None
    KSS_AVAILABLE = False
    KSS_ERROR = str(e)


# =========================================================
# Path Config
# =========================================================

INPUT_BASE_DIR = Path("preprocessing/cleaned")
OUTPUT_BASE_DIR = Path("preprocessing/results")

CATEGORIES = [
    "card",
    "deposit",
    "insurance",
]


# =========================================================
# 0. Optional Library Status
# =========================================================

def print_library_status() -> None:
    """
    선택 라이브러리 사용 가능 여부를 터미널에 출력한다.
    """

    print("=" * 60)
    print("[청크 생성 실행 환경 확인]")

    if USE_KSS and KSS_AVAILABLE:
        print("kss: 사용 가능")
    elif USE_KSS and not KSS_AVAILABLE:
        print("kss: 사용 불가 -> 정규식 기반 문장 분리 사용")
        print(f"kss 상태: {KSS_ERROR}")
    else:
        print("kss: 사용 안 함")

    print("=" * 60)


# =========================================================
# 1. 구조 판단 함수
# =========================================================

def is_heading(line: str) -> bool:
    """
    제목/소제목/조항으로 보이는 줄인지 판단한다.
    특정 상품명보다 구조적 패턴 중심으로 판단한다.
    """

    patterns = [
        r"^[가-하]\.",
        r"^◇",
        r"^○",
        r"^[①②③④⑤⑥⑦⑧⑨⑩]",
        r"^Ⅰ\.",
        r"^Ⅱ\.",
        r"^Ⅲ\.",
        r"^Ⅳ\.",
        r"^Ⅴ\.",
        r"^V\.",
        r"^Ⅵ\.",
        r"^Ⅶ\.",
        r"^Ⅷ\.",
        r"^Ⅸ\.",
        r"^제\d+편",
        r"^제\d+장",
        r"^제\d+절",
        r"^제\d+조(?:의\d+)?\s*\([^)]+\)",
        r"^<별표",
        r"^<부표",
        r"^<붙임",
        r"^\[붙임\]",
        r"^▶",
        r"^주\s*\d+\)",
        r"^주\d+\)",
        r"^※",
        r"^Q\s*>",
        r"^A\s*>",
        r"^Q\)",
        r"^A\)",

        # 금융 문서 공통 제목 패턴
        r"^상품",
        r"^보험",
        r"^보장",
        r"^약관",
        r"^계약",
        r"^거래",
        r"^가입",
        r"^발급",
        r"^연회비",
        r"^유의사항",
        r"^주의사항",
        r"^확인사항",
        r"^비과세",
        r"^소득공제",
        r"^이율",
        r"^금리",
        r"^수수료",
        r"^예금",
        r"^대출",
        r"^청약",
        r"^해지",
        r"^만기",
        r"^민원",
        r"^분쟁",
        r"^예금자 보호",
        r"^부가서비스",
        r"^할인",
        r"^해외 이용",
        r"^후불",
        r"^체크카드",
        r"^기타",

        # 카드 설명서
        r"^선택형",
        r"^A팩",
        r"^B팩",
        r"^OTT",
        r"^APP",
        r"^여가",
        r"^교통",
        r"^편의점",
        r"^영화",
        r"^쇼핑 멤버십",
        r"^통신요금",
        r"^패션/라이프",
        r"^패션/ 라이프",
        r"^배달",
        r"^데이트",
        r"^할인 서비스",
        r"^전월 이용실적",
        r"^해외 이용",
        r"^일반 가맹점 이용",
        r"^무승인/T&E 업종 이용",
        r"^국제브랜드",
        r"^후불교통",
        r"^직불 이용한도",
        r"^비접촉식",
        r"^연체이자율",

        # 실손보험/보험 설명서
        r"^기본계약",
        r"^의무부가 특약",
        r"^기본형",
        r"^특약",
        r"^갱신형",
        r"^주요 용어",
        r"^보험료 차등적용",
        r"^해외 장기체류자",
        r"^보험금 지급제한",
        r"^보험료 산출기초",
        r"^보험가격지수",
        r"^보험료 예시",
        r"^해약환급금",
        r"^상해급여",
        r"^질병급여",
        r"^상해비급여",
        r"^질병비급여",
        r"^3대 비급여",
        r"^비급여 보험금",
        r"^요율 상대도",
        r"^연간 보험가입금액",
    ]

    return any(re.search(pattern, line) for pattern in patterns)


def is_bullet(line: str) -> bool:
    """
    bullet 항목인지 판단한다.
    """

    patterns = [
        r"^-",
        r"^ㅇ",
        r"^∙",
        r"^•",
        r"^\d+\.",
        r"^\d+\)",
        r"^\(\d+\)",
        r"^[가-하]\.",
        r"^Q\)",
        r"^A\)",
        r"^\[\d+\]",
        r"^01\)",
        r"^02\)",
        r"^03\)",
        r"^04\)",
        r"^05\)",
        r"^06\)",
        r"^07\)",
    ]

    return any(re.search(pattern, line) for pattern in patterns)


def is_table_like_line(line: str) -> bool:
    """
    표에서 나온 줄로 보이는지 범용적으로 판단한다.
    특정 상품명보다는 표 구조와 금융 키워드 중심으로 판단한다.
    """

    table_keywords = [
        # 공통 표성 표현
        "구분",
        "내용",
        "유의사항",
        "확인사항",
        "가입대상",
        "가입 대상",
        "발급대상",
        "발급 대상",
        "연회비",
        "브랜드",
        "상품 특징",
        "상품 유형",
        "적립방법",
        "납입기간",
        "가입기간",
        "적용이율",
        "이율",
        "금리",
        "수수료",
        "할인율",
        "할인한도",
        "할인 한도",
        "월 할인한도",
        "월 할인 한도",
        "전월 이용실적",
        "지급사유",
        "지급금액",
        "지급 사유",
        "지급 금액",
        "보장내용",
        "보상한도",
        "보험기간",
        "보험료",
        "보험가입금액",
        "공제금액",
        "해약환급금",
        "예금자보호",
        "예금담보대출",
        "중도해지",
        "만기",
        "비과세",
        "소득공제",
        "제출 서류",
        "필요 서류",
        "거래방법",
        "청구 절차",
        "민원처리",
        "분쟁조정",
        "출금 시점",
        "적용 환율",
        "차액 환급",
        "차액 추가 출금",

        # 카드 혜택표/해외이용
        "선택형",
        "A팩",
        "B팩",
        "OTT",
        "APP",
        "여가",
        "교통",
        "편의점",
        "영화",
        "쇼핑 멤버십",
        "통신요금",
        "패션/라이프",
        "패션/ 라이프",
        "배달",
        "데이트",
        "할인 서비스",
        "환급 할인",
        "해외 이용",
        "해외 서비스 수수료",
        "국제브랜드 수수료",
        "전신환 매도율",
        "일반 가맹점 이용",
        "무승인/T&E 업종 이용",
        "부가서비스 변경",
        "연체이자율",
        "후불교통",
        "후불교통 기능",
        "직불 이용한도",
        "비접촉식",
        "서비스 할인율",
        "할인 금액",
        "청구금액 산출방법",
        "승인금액",
        "매입금액",
        "출금계좌",
        "적용환율",

        # 실손보험/의료비 표성 표현
        "기본형",
        "특약",
        "갱신형",
        "기본계약",
        "의무부가 특약",
        "상해급여",
        "질병급여",
        "상해비급여",
        "질병비급여",
        "3대 비급여",
        "실손의료비",
        "급여실손의료비",
        "비급여실손의료비",
        "상해급여실손의료비",
        "질병급여실손의료비",
        "상해비급여실손의료비",
        "질병비급여실손의료비",
        "3대 비급여 실손의료비",
        "비급여보험금",
        "비급여 보험금",
        "비급여 보험금 판정기간",
        "요율상대도",
        "요율 상대도",
        "입원",
        "통원",
        "통원 1회당",
        "상급병실료차액",
        "상급병실료 차액",
        "도수치료",
        "체외충격파치료",
        "증식치료",
        "주사료",
        "자기공명영상진단",
        "연간 보험가입금액",
        "입통원 합산한도",
        "입·통원 합산한도",
        "통원 한도",
        "보험가격지수",
        "경과 년수",
        "경과년 수",
        "총납입보험료",
        "총 납입보험료",
        "해약 환급금",
        "해약환급금",
        "예정이율",
        "예정위험률",
        "예정사업비율",
    ]

    if line in table_keywords:
        return True

    if any(keyword in line for keyword in table_keywords):
        if len(line) <= 300:
            return True

    number_count = len(re.findall(r"\d", line))
    money_or_rate_count = len(re.findall(r"원|만원|억원|천만원|%|연\s*\d", line))

    if number_count >= 3 and money_or_rate_count >= 1:
        return True

    amount_count = len(re.findall(r"\d+(?:,\d+)*\s*(?:원|만원|억원|%)", line))
    if amount_count >= 2:
        return True

    return False


# =========================================================
# 2. 뭉친 줄 분리 함수
# =========================================================

def split_compact_line(line: str) -> list[str]:
    """
    OCR/PDF 때문에 한 줄에 여러 항목이 붙은 경우 범용적으로 분리한다.
    카드 혜택표, 해외이용 수수료표, 예금/보험 표성 문장을 함께 처리한다.
    """

    # 큰 구역 먼저 분리
    section_patterns = [
        # 카드
        r"선택형\s*\[A팩\]",
        r"선택형\s*\[B팩\]",
        r"선택형\(A팩/B팩\)",
        r"할인 서비스 적용 안내",
        r"전월 이용실적 기준",
        r"전월 이용실적 제외 대상",
        r"체크카드 확인사항",
        r"체크카드 해외 이용 시 유의사항",
        r"선택서비스 안내사항",
        r"해외 이용 관련 수수료",
        r"해외 이용 시 청구금액",
        r"일반 가맹점 이용",
        r"무승인/T&E 업종 이용",
        r"발급대상/브랜드/연회비",
        r"부가서비스 변경 안내",
        r"연체이자율",
        r"기타 공통 확인사항",
        r"후불교통 기능",
        r"체크카드 직불 이용한도",
        r"체크카드 이용 제한",

        # 실손보험
        r"기본계약",
        r"의무부가 특약",
        r"상해급여실손의료비",
        r"질병급여실손의료비",
        r"상해비급여실손의료비",
        r"질병비급여실손의료비",
        r"3대 비급여 실손의료비",
        r"주요 용어",
        r"보험료 차등적용",
        r"보험금 지급제한",
        r"보험료 산출기초",
        r"보험가격지수",
        r"보험료 예시",
        r"해약환급금",
    ]

    for pattern in section_patterns:
        line = re.sub(rf"\s*({pattern})", r"\n\1", line)

    # 짧은 단어는 너무 공격적으로 분리하면 문장이 깨지므로 표 헤더/큰 라벨 중심으로만 분리
    split_keywords = [
        # 공통 표 헤더
        "지급사유",
        "지급금액",
        "지급 사유",
        "지급 금액",
        "보장내용",
        "보상한도",
        "보험가입금액",
        "공제금액",
        "보험기간",
        "보험료 납입기간",
        "가입나이",
        "가입대상",
        "가입 대상",
        "적립방법",
        "납입기간",
        "적용이율",
        "중도해지",
        "예금자보호",
        "예금담보대출",
        "이자 지급",
        "가입기간",

        # 카드
        "발급대상",
        "발급 대상",
        "전월 이용실적",
        "서비스 할인율",
        "월 할인 한도",
        "월 할인한도",
        "청구금액 산출방법",
        "국제브랜드 수수료",
        "해외 서비스 수수료",
        "전신환 매도율",
        "차액 환급",
        "차액 추가 출금",
        "승인금액",
        "매입금액",
        "출금 시점",
        "적용환율",
        "적용 환율",

        # 실손보험
        "상해급여실손의료비",
        "질병급여실손의료비",
        "상해비급여실손의료비",
        "질병비급여실손의료비",
        "3대 비급여 실손의료비",
        "급여실손의료비",
        "비급여실손의료비",
        "비급여 보험금 판정기간",
        "비급여 보험금",
        "비급여보험금",
        "요율 상대도",
        "요율상대도",
        "연간 보험가입금액",
        "입·통원 합산한도",
        "입통원 합산한도",
        "상급병실료차액",
        "상급병실료 차액",
        "도수치료",
        "체외충격파치료",
        "증식치료",
        "자기공명영상진단",
        "총납입보험료",
        "총 납입보험료",
        "해약환급금",
        "해약 환급금",
    ]

    split_keywords = sorted(set(split_keywords), key=len, reverse=True)

    for keyword in split_keywords:
        # 이미 줄 시작이면 중복 개행을 만들지 않도록 처리
        line = re.sub(rf"(?<!\n)\s*({re.escape(keyword)})", r"\n\1", line)

    parts = [part.strip() for part in line.split("\n") if part.strip()]

    # 너무 짧은 라벨만 따로 떨어진 경우 다음 내용과 합치기
    label_only = {
        "OTT",
        "APP",
        "여가",
        "교통",
        "편의점",
        "영화",
        "배달",
        "데이트",
        "브랜드",
        "연회비",
        "수수료",
        "A팩",
        "B팩",
        "입원",
        "통원",
        "특약",
        "갱신형",
        "기본형",
    }

    merged = []
    i = 0

    while i < len(parts):
        current = parts[i]

        if i + 1 < len(parts) and current in label_only:
            merged.append(f"{current} {parts[i + 1]}".strip())
            i += 2
        else:
            merged.append(current)
            i += 1

    return merged


def split_policy_article_line(line: str) -> list[str]:
    """
    한 줄에 여러 조항/편/장/절/항목이 붙어 있는 경우 분리한다.
    """

    line = re.sub(r"\s+(제\d+편)", r"\n\1", line)
    line = re.sub(r"\s+(제\d+장)", r"\n\1", line)
    line = re.sub(r"\s+(제\d+절)", r"\n\1", line)
    line = re.sub(r"\s+(제\d+조(?:의\d+)?\s*\([^)]+\))", r"\n\1", line)

    line = re.sub(r"\s+([가-하]\.)\s+", r"\n\1 ", line)
    line = re.sub(r"\s+(\(\d+\))", r"\n\1", line)
    line = re.sub(r"\s+([①②③④⑤⑥⑦⑧⑨⑩])", r"\n\1", line)

    return [part.strip() for part in line.split("\n") if part.strip()]


# =========================================================
# 3. 문장 분리
# =========================================================

def split_sentences(text: str) -> list[str]:
    """
    일반 문단을 문장 단위로 분리한다.
    """

    text = re.sub(r"\s{2,}", " ", text).strip()

    if not text:
        return []

    if USE_KSS and KSS_AVAILABLE:
        try:
            return [sent.strip() for sent in kss.split_sentences(text) if sent.strip()]
        except Exception:
            pass

    pattern = r"(?<=[.!?]|다\.|요\.|까\.|함\.|음\.)\s+"
    return [sent.strip() for sent in re.split(pattern, text) if sent.strip()]


# =========================================================
# 4. chunk 유효성 검사
# =========================================================

def is_valid_chunk(chunk: str) -> bool:
    """
    저장할 만한 chunk인지 판단한다.
    """

    chunk = chunk.strip()

    if not chunk:
        return False

    if len(chunk) < 3:
        return False

    if not re.search(r"[가-힣A-Za-z]", chunk):
        return False

    if re.fullmatch(r"\d+", chunk):
        return False

    if re.fullmatch(r"[-_=*·•●○\s]+", chunk):
        return False

    return True


# =========================================================
# 5. chunk 생성
# =========================================================

def make_chunks_from_text(text: str) -> list[str]:
    """
    cleaned text를 chunk 리스트로 변환한다.
    """

    lines = [line.strip() for line in text.split("\n")]

    # (2), (7) 같은 번호만 단독으로 떨어진 줄은 다음 줄과 합친다.
    merged_lines = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if re.fullmatch(r"\(\d+\)", line) and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            merged_lines.append(f"{line} {next_line}".strip())
            i += 2
            continue

        merged_lines.append(line)
        i += 1

    lines = merged_lines

    chunks = []
    paragraph_buffer = []

    def flush_paragraph_buffer():
        nonlocal paragraph_buffer, chunks

        if not paragraph_buffer:
            return

        paragraph = " ".join(paragraph_buffer).strip()
        paragraph_buffer = []

        article_parts = split_policy_article_line(paragraph)

        for part in article_parts:
            if is_heading(part) or is_bullet(part) or is_table_like_line(part):
                if is_valid_chunk(part):
                    chunks.append(part)
                continue

            sentences = split_sentences(part)

            for sent in sentences:
                if is_valid_chunk(sent):
                    chunks.append(sent)

    for line in lines:
        if not line:
            flush_paragraph_buffer()
            continue

        # 조항이 한 줄에 여러 개 붙은 경우
        if re.search(r"제\d+(편|장|절|조)", line):
            split_parts = split_policy_article_line(line)

            if len(split_parts) > 1:
                flush_paragraph_buffer()

                for part in split_parts:
                    if is_valid_chunk(part):
                        chunks.append(part)

                continue

        # 표/혜택/거래조건 등이 한 줄에 뭉친 경우
        if is_table_like_line(line) and len(line) > 80:
            flush_paragraph_buffer()

            for part in split_compact_line(line):
                if is_valid_chunk(part):
                    chunks.append(part)

            continue

        # 제목/항목/표 줄은 그대로 저장
        if is_heading(line) or is_bullet(line) or is_table_like_line(line):
            flush_paragraph_buffer()

            if is_valid_chunk(line):
                chunks.append(line)

            continue

        paragraph_buffer.append(line)

    flush_paragraph_buffer()

    return postprocess_chunks(chunks)


# =========================================================
# 6. chunk 후처리
# =========================================================

def postprocess_chunks(chunks: list[str]) -> list[str]:
    """
    chunk 리스트를 최종 정리한다.
    """

    result = []

    remove_exact = {
        "보험약관 안내문 목차 유의사항 주요 내용 요약",
        "자동차보험의 구성 보상하는 내용 보험금, 손해배상 청구 일반사항 보험금 지급기준 붙임",
    }

    for chunk in chunks:
        chunk = chunk.strip()
        chunk = re.sub(r"\s{2,}", " ", chunk)

        chunk = re.sub(r"^-\s*", "- ", chunk)
        chunk = re.sub(r"^∙\s*", "∙ ", chunk)

        chunk = re.sub(r"[·.]{3,}\s*\d{1,3}\s*$", "", chunk).strip()

        if chunk in remove_exact:
            continue

        if is_heading(chunk) or is_table_like_line(chunk):
            chunk = re.sub(r"\s+\d{1,3}\s*$", "", chunk).strip()

        if is_valid_chunk(chunk):
            result.append(chunk)

    # 연속 중복 제거
    deduped = []
    prev = None

    for chunk in result:
        if chunk == prev:
            continue

        deduped.append(chunk)
        prev = chunk

    return deduped


# =========================================================
# 7. 파일 처리
# =========================================================

def process_file(input_path: Path, output_path: Path) -> None:
    """
    cleaned txt 파일 하나를 chunk txt로 저장한다.
    """

    with open(input_path, "r", encoding="utf-8") as f:
        cleaned_text = f.read()

    chunks = make_chunks_from_text(cleaned_text)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(chunk + "\n")

    display_name = input_path.stem.replace("_cleaned", "")
    print(f"{display_name} -> 청크 수: {len(chunks)}")


def process_category(category: str) -> None:
    """
    카테고리 폴더 안의 cleaned txt 파일을 모두 chunk로 변환한다.
    """

    input_dir = INPUT_BASE_DIR / category
    output_dir = OUTPUT_BASE_DIR / category

    if not input_dir.exists():
        return

    txt_files = list(input_dir.glob("*_cleaned.txt"))

    if not txt_files:
        return

    for input_path in txt_files:
        output_name = input_path.stem.replace("_cleaned", "") + "_chunks.txt"
        output_path = output_dir / output_name
        process_file(input_path, output_path)


def main() -> None:
    """
    전체 카테고리 chunk 생성 실행
    """

    print_library_status()

    for category in CATEGORIES:
        process_category(category)


if __name__ == "__main__":
    main()