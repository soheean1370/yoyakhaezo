import os
import re
from pathlib import Path

from dotenv import load_dotenv
from FlagEmbedding import BGEM3FlagModel
from supabase import create_client
from tqdm import tqdm

from make_chunks import (
    is_heading,
    is_bullet,
    is_table_like_line,
    split_compact_line,
    split_policy_article_line,
    is_valid_chunk,
)


# =========================================================
# 1. 환경변수 로드
# =========================================================

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL이 .env에 없습니다.")

if not SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError("SUPABASE_SERVICE_ROLE_KEY가 .env에 없습니다.")


# =========================================================
# 2. Supabase / Embedding Model Lazy Loading
# =========================================================

supabase = None
model = None


def get_supabase():
    global supabase

    if supabase is None:
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

    return supabase


def get_model():
    global model

    if model is None:
        model = BGEM3FlagModel(
            "BAAI/bge-m3",
            use_fp16=False
        )

    return model


# =========================================================
# 3. 경로 및 상수 설정
# =========================================================

BASE_DIR = Path("preprocessing/results")
CATEGORIES = ["card", "deposit", "insurance"]

EMBEDDING_MODEL_NAME = "BAAI/bge-m3"
EMBEDDING_DIM = 1024

MAX_SECTION_CHARS = 1200
EMBEDDING_BATCH_SIZE = 8
SUPABASE_BATCH_SIZE = 50

# title_path를 content 앞에 붙이면 상품명/section 문맥까지 embedding에 반영됨
INCLUDE_TITLE_PATH_IN_CONTENT = True


# =========================================================
# 4. 한 줄 안에 붙은 제목 분리용 키워드
# =========================================================

INLINE_SECTION_HEADINGS = [
    # 공통
    "상품 개요 및 특징",
    "상품 개요",
    "상품 특징",
    "상품명",
    "가입대상",
    "가입 대상",
    "가입기간",
    "가입 기간",
    "가입금액",
    "가입 금액",
    "거래방법",
    "거래 방법",
    "예금자보호",
    "비과세",
    "소득공제",
    "유의사항",
    "주의사항",
    "확인사항",
    "기타 안내",
    "민원 접수 안내",

    # 카드
    "기본 및 추가 혜택 공통 유의사항",
    "라운지 및 발레파킹 서비스 공통 유의사항",
    "해외 원화 결제 차단 서비스 신청 방법",
    "해외 이용 시 청구 금액 산출 방법",
    "공항 및 특급호텔 발레파킹 무료 이용",
    "THE LOUNGE : 공항 라운지 무료 이용",
    "카드 이용 유의사항",
    "해외 결제 이용 안내",
    "가족 카드 이용 안내",
    "이용 금액 합산 제외 기준",
    "이용 금액 산정 기준",
    "혜택 제공 기준",
    "적립 제외 기준",
    "M포인트 적립 기준",
    "M포인트 사용 안내",
    "M포인트 사용 기준",
    "연간 보너스 바우처",
    "제공 및 사용 기준",
    "메탈 플레이트 제공",
    "기본 혜택",
    "추가 혜택",
    "우대 서비스",
    "연회비",
    "연체 금리",
    "적립 대상",
    "적립 시기",
    "유효 기간",
    "사용 및 관리 기준",
    "사용 방법",
    "사용 취소",
    "사용 제한",
    "연간 한도",
    "가족 합산",
    "M포인트 상속",
    "M포인트 조회",
    "M포인트 사용",

    # 예금 / 적금
    "기본금리",
    "우대금리",
    "우대 금리",
    "우대 조건",
    "적용이율",
    "이자 지급",
    "중도해지",
    "중도해지이율",
    "만기 후 이율",
    "만기 후 금리",
    "예금담보대출",

    # 보험
    "보험금을 지급하지 아니하는 사유",
    "보험금을 지급하지 않는 사유",
    "보험금 지급제한",
    "보험료 산출기초",
    "보험가격지수",
    "보험료 예시",
    "해약환급금",
    "기본계약",
    "의무부가 특약",
    "상해급여",
    "질병급여",
    "상해비급여",
    "질병비급여",
    "3대 비급여",
    "주요 용어",
    "보장내용",
    "보장 내용",
    "지급사유",
    "지급금액",
    "보상한도",
    "공제금액",
    "보험가입금액",
    "보험기간",
    "납입기간",
]


# =========================================================
# 5. 범용 제목 계층 판단용 키워드
# =========================================================

GENERIC_MAJOR_KEYWORDS = [
    # 공통
    "상품",
    "상품 개요",
    "상품 특징",
    "가입",
    "가입대상",
    "가입기간",
    "가입금액",
    "거래",
    "거래방법",
    "계약",
    "해지",
    "만기",
    "예금자보호",
    "비과세",
    "소득공제",

    # 카드
    "연회비",
    "기본 혜택",
    "추가 혜택",
    "혜택 제공 기준",
    "연간 보너스 바우처",
    "M포인트 사용",
    "카드 이용 유의사항",
    "우대 서비스",
    "연체 금리",

    # 예금/적금
    "금리",
    "이율",
    "기본금리",
    "우대금리",
    "우대 금리",
    "중도해지",
    "중도해지이율",
    "만기 후 이율",
    "만기 후 금리",

    # 보험
    "보험",
    "보장",
    "보장내용",
    "보험료",
    "보험금",
    "보험금 지급제한",
    "보험료 산출기초",
    "보험가격지수",
    "보험료 예시",
    "해약환급금",
    "기본계약",
    "특약",
]


GENERIC_SUB_KEYWORDS = [
    # 공통
    "대상",
    "기준",
    "조건",
    "한도",
    "방법",
    "절차",
    "서류",
    "산정 기준",
    "제외 기준",
    "합산 제외 기준",

    # 카드
    "이용 금액 산정 기준",
    "이용 금액 합산 제외 기준",
    "적립 대상",
    "적립 제외 기준",
    "적립 시기",
    "해외 결제 이용 안내",
    "해외 이용 시 청구 금액 산출 방법",
    "해외 원화 결제 차단 서비스 신청 방법",
    "가족 카드 이용 안내",
    "민원 접수 안내",

    # 예금/적금
    "적용이율",
    "우대 조건",
    "이자 지급",
    "중도해지이율",
    "만기 후 금리",

    # 보험
    "지급사유",
    "지급금액",
    "보상한도",
    "공제금액",
    "보험가입금액",
    "보험기간",
    "납입기간",
]


GENERIC_MINOR_KEYWORDS = [
    "유의사항",
    "주의사항",
    "확인사항",
    "기타 안내",
    "제공 및 사용 기준",
    "사용 및 관리 기준",
    "사용 방법",
    "사용 취소",
    "사용 제한",
    "연간 한도",
    "가족 합산",
]


# =========================================================
# 6. 상품명 감지용 키워드
# =========================================================

PRODUCT_TYPE_KEYWORDS = [
    # 카드
    "카드",
    "Card",
    "CARD",
    "Visa",
    "Master",
    "현대카드",
    "삼성카드",
    "신한카드",
    "국민카드",
    "KB국민카드",
    "롯데카드",
    "우리카드",
    "하나카드",
    "NH농협카드",

    # 예금/적금
    "예금",
    "적금",
    "입출금",
    "통장",
    "파킹통장",
    "정기예금",
    "정기적금",
    "자유적금",

    # 보험
    "보험",
    "실손",
    "의료비",
    "암보험",
    "건강보험",
    "상해보험",
    "운전자보험",
    "종신보험",
]


# =========================================================
# 7. 제목 판단 보조 함수
# =========================================================

def normalize_glued_headings(line: str) -> str:
    replacements = {
        # 카드
        "혜택 제공 기준이용 금액 산정 기준": "혜택 제공 기준 이용 금액 산정 기준",
        "이용 금액 합산 제외 기준이용 금액 산정 기준": "이용 금액 합산 제외 기준 이용 금액 산정 기준",
        "카드 이용 유의사항가족 카드 이용 안내": "카드 이용 유의사항 가족 카드 이용 안내",
        "카드 이용 유의사항해외 결제 이용 안내": "카드 이용 유의사항 해외 결제 이용 안내",
        "해외 결제 이용 안내해외 이용 시 청구 금액 산출 방법": "해외 결제 이용 안내 해외 이용 시 청구 금액 산출 방법",
        "M포인트 사용 안내M포인트 사용 기준": "M포인트 사용 안내 M포인트 사용 기준",
        "기본 혜택추가 혜택": "기본 혜택 추가 혜택",
        "유의사항기본 혜택": "유의사항 기본 혜택",
        "유의사항가족 카드 이용 안내": "유의사항 가족 카드 이용 안내",

        # 예금/적금
        "상품 개요가입대상": "상품 개요 가입대상",
        "가입대상가입기간": "가입대상 가입기간",
        "가입기간가입금액": "가입기간 가입금액",
        "기본금리우대금리": "기본금리 우대금리",
        "중도해지만기 후 이율": "중도해지 만기 후 이율",

        # 보험
        "보험금 지급제한보험금을 지급하지 않는 사유": "보험금 지급제한 보험금을 지급하지 않는 사유",
        "보험료 산출기초보험가격지수": "보험료 산출기초 보험가격지수",
        "보험료 예시해약환급금": "보험료 예시 해약환급금",
        "기본계약의무부가 특약": "기본계약 의무부가 특약",
    }

    for old, new in replacements.items():
        line = line.replace(old, new)

    return line


def has_value_expression(line: str) -> bool:
    return bool(
        re.search(
            r"\d+(?:,\d+)*\s*(원|만원|천만원|억원|%|회|개월|년|일|세)",
            line,
        )
    )


def is_sentence_like(line: str) -> bool:
    sentence_end_patterns = [
        r"다\.?$",
        r"합니다\.?$",
        r"됩니다\.?$",
        r"있습니다\.?$",
        r"없습니다\.?$",
        r"바랍니다\.?$",
        r"가능합니다\.?$",
        r"불가합니다\.?$",
        r"제외됩니다\.?$",
        r"제공됩니다\.?$",
        r"적용됩니다\.?$",
        r"청구됩니다\.?$",
        r"지급합니다\.?$",
        r"보장합니다\.?$",
    ]

    return any(re.search(pattern, line) for pattern in sentence_end_patterns)


def is_article_heading(line: str) -> bool:
    patterns = [
        r"^제\d+편",
        r"^제\d+장",
        r"^제\d+절",
        r"^제\d+조",
        r"^<별표",
        r"^<부표",
        r"^<붙임",
        r"^\[붙임\]",
    ]

    return any(re.search(pattern, line) for pattern in patterns)


def is_section_heading(line: str) -> bool:
    line = line.strip()

    if not line:
        return False

    if is_article_heading(line):
        return True

    if len(line) > 80:
        return False

    if is_bullet(line):
        return False

    if line in INLINE_SECTION_HEADINGS:
        return True

    if is_heading(line):
        if has_value_expression(line):
            return False

        if is_sentence_like(line):
            return False

        return True

    if len(line) <= 25:
        if has_value_expression(line):
            return False

        if is_sentence_like(line):
            return False

        heading_like_keywords = [
            "혜택",
            "유의사항",
            "주의사항",
            "확인사항",
            "기준",
            "안내",
            "금리",
            "이율",
            "수수료",
            "연회비",
            "보험료",
            "보험금",
            "해지",
            "환급",
            "적립",
            "사용",
            "한도",
            "대상",
            "조건",
            "만기",
            "가입",
            "보장",
            "납입",
            "지급",
            "보상",
            "공제",
        ]

        if any(keyword in line for keyword in heading_like_keywords):
            return True

        return False

    return False


def get_heading_level(line: str) -> int:
    line = line.strip()

    if not is_section_heading(line):
        return 0

    if is_article_heading(line):
        return 1

    if line in GENERIC_MINOR_KEYWORDS:
        return 3

    if line in GENERIC_MAJOR_KEYWORDS:
        return 1

    if line in GENERIC_SUB_KEYWORDS:
        return 2

    if any(keyword in line for keyword in GENERIC_MINOR_KEYWORDS):
        return 3

    if any(keyword in line for keyword in GENERIC_SUB_KEYWORDS):
        return 2

    if any(keyword in line for keyword in GENERIC_MAJOR_KEYWORDS):
        return 1

    return 2


def is_known_heading_label(line: str) -> bool:
    """
    명확한 구조 제목인지 판단한다.
    상품명 후보에서 제외하기 위해 사용한다.
    """
    if is_article_heading(line):
        return True

    if line in INLINE_SECTION_HEADINGS:
        return True

    if line in GENERIC_MAJOR_KEYWORDS:
        return True

    if line in GENERIC_SUB_KEYWORDS:
        return True

    if line in GENERIC_MINOR_KEYWORDS:
        return True

    return False


def looks_like_product_title(line: str) -> bool:
    """
    한 줄 자체가 상품명처럼 보이는지 판단한다.
    """
    line = line.strip()

    if not line:
        return False

    if len(line) > 80:
        return False

    if is_bullet(line):
        return False

    if has_value_expression(line):
        return False

    if is_sentence_like(line):
        return False

    if is_known_heading_label(line):
        return False

    # 상품명에는 영어/숫자/브랜드/금융상품 키워드가 섞이는 경우가 많다.
    if any(keyword in line for keyword in PRODUCT_TYPE_KEYWORDS):
        return True

    # the Orange, MY WE:SH, iD GLOBAL 같은 카드명 대응
    has_english = bool(re.search(r"[A-Za-z]", line))
    has_korean = bool(re.search(r"[가-힣]", line))

    if has_english and len(line) <= 40:
        return True

    # 한국어 상품명 대응: 짧고 명사형이며 문장/값이 아니면 후보
    if has_korean and len(line) <= 40:
        return True

    return False


def has_following_heading(lines: list[str], index: int, lookahead: int = 3) -> bool:
    """
    현재 줄 다음 몇 줄 안에 section heading이 있는지 확인한다.
    상품명은 보통 바로 아래에 연회비/금리/보장내용 같은 제목이 온다.
    """
    end = min(len(lines), index + lookahead + 1)

    for next_idx in range(index + 1, end):
        next_line = lines[next_idx].strip()

        if not next_line:
            continue

        if is_section_heading(next_line):
            return True

    return False


def is_product_title_candidate(lines: list[str], index: int) -> bool:
    """
    한 문서 안에서 상품이 바뀌는 지점을 감지한다.

    판단 기준:
    - 현재 줄이 상품명처럼 보임
    - 다음 1~3줄 안에 section heading이 있음
    """
    line = lines[index].strip()

    if not looks_like_product_title(line):
        return False

    if not has_following_heading(lines, index, lookahead=3):
        return False

    return True


# =========================================================
# 8. 한 줄 안에 붙은 제목 분리
# =========================================================

def split_inline_section_headings(line: str) -> list[str]:
    line = line.strip()
    line = normalize_glued_headings(line)

    if not line:
        return []

    headings = sorted(set(INLINE_SECTION_HEADINGS), key=len, reverse=True)

    matches = []

    for heading in headings:
        pattern = re.escape(heading)

        for match in re.finditer(pattern, line):
            start = match.start()
            end = match.end()

            before_ok = start == 0 or line[start - 1].isspace()
            after_ok = end == len(line) or line[end:end + 1].isspace()

            if before_ok and after_ok:
                matches.append((start, end, heading))

    if not matches:
        return [line]

    matches.sort(key=lambda x: (x[0], -(x[1] - x[0])))

    filtered = []
    occupied_until = -1

    for start, end, heading in matches:
        if start < occupied_until:
            continue

        filtered.append((start, end, heading))
        occupied_until = end

    parts = []
    cursor = 0

    for idx, (start, end, heading) in enumerate(filtered):
        if start > cursor:
            before_text = line[cursor:start].strip()
            if before_text:
                parts.append(before_text)

        parts.append(heading)

        next_start = filtered[idx + 1][0] if idx + 1 < len(filtered) else len(line)
        after_text = line[end:next_start].strip()

        if after_text:
            parts.append(after_text)

        cursor = next_start

    if cursor < len(line):
        tail = line[cursor:].strip()
        if tail:
            parts.append(tail)

    return [part.strip() for part in parts if part.strip()]


# =========================================================
# 9. 기존 chunk 파일 읽기 + 확장 분리
# =========================================================

def read_and_expand_chunk_lines(file_path: Path) -> list[str]:
    expanded_lines = []

    with open(file_path, "r", encoding="utf-8") as f:
        raw_lines = [line.strip() for line in f if line.strip()]

    for line in raw_lines:
        line = normalize_glued_headings(line)

        article_parts = split_policy_article_line(line)

        for article_part in article_parts:
            if is_table_like_line(article_part) and len(article_part) > 80:
                compact_parts = split_compact_line(article_part)
            else:
                compact_parts = [article_part]

            for compact_part in compact_parts:
                inline_parts = split_inline_section_headings(compact_part)

                for part in inline_parts:
                    part = part.strip()

                    if is_valid_chunk(part):
                        expanded_lines.append(part)

    return expanded_lines


# =========================================================
# 10. 제목 + 내용 section 단위 재병합
# =========================================================

def merge_lines_into_sections(
    lines: list[str],
    max_chars: int = MAX_SECTION_CHARS,
) -> list[dict]:
    """
    상품명 변경까지 고려하여 section을 병합한다.

    구조:
    root_title = 현재 상품명
    level2_title = 현재 상품 안의 주요 section
    section_title = 현재 section 제목
    title_path = root_title > level2_title > section_title
    """

    sections = []

    if not lines:
        return sections

    root_title = None
    level1_title = None
    level2_title = None

    current_lines = []
    current_start_line = 0
    current_title = None

    current_level1_title = None
    current_level2_title = None

    def make_title_path(
        l1: str | None,
        l2: str | None,
        title: str | None
    ) -> str | None:
        parts = []

        for value in [l1, l2, title]:
            if value and value not in parts:
                parts.append(value)

        if not parts:
            return None

        return " > ".join(parts)

    def flush(end_line: int):
        nonlocal current_lines, current_start_line, current_title
        nonlocal current_level1_title, current_level2_title

        if not current_lines:
            return

        content = "\n".join(current_lines).strip()

        if content:
            sections.append({
                "content": content,
                "start_line": current_start_line,
                "end_line": end_line,
                "section_title": current_title,
                "parent_title": current_level2_title or current_level1_title,
                "level1_title": current_level1_title,
                "level2_title": current_level2_title,
                "root_title": current_level1_title,
                "title_path": make_title_path(
                    current_level1_title,
                    current_level2_title,
                    current_title,
                ),
            })

        current_lines = []
        current_start_line = 0
        current_title = None
        current_level1_title = level1_title
        current_level2_title = level2_title

    for idx, line in enumerate(lines):
        line = line.strip()

        if not line:
            continue

        # 상품명 감지: 첫 상품 또는 중간 상품 변경
        if is_product_title_candidate(lines, idx):
            if current_lines:
                flush(end_line=idx - 1)

            root_title = line
            level1_title = root_title
            level2_title = None

            current_lines = []
            current_start_line = idx + 1
            current_title = None
            current_level1_title = level1_title
            current_level2_title = None
            continue

        # 아직 상품명이 없다면 첫 유효 줄을 root_title로 사용
        if root_title is None:
            root_title = line
            level1_title = root_title
            level2_title = None

            current_level1_title = level1_title
            current_level2_title = None
            continue

        heading_level = get_heading_level(line)

        if heading_level > 0 and current_lines:
            flush(end_line=idx - 1)

        if heading_level == 1:
            level2_title = line

            current_lines = [line]
            current_start_line = idx
            current_title = line
            current_level1_title = level1_title
            current_level2_title = level2_title
            continue

        if heading_level == 2:
            level2_title = line

            current_lines = [line]
            current_start_line = idx
            current_title = line
            current_level1_title = level1_title
            current_level2_title = level2_title
            continue

        if heading_level == 3:
            current_lines = [line]
            current_start_line = idx
            current_title = line
            current_level1_title = level1_title
            current_level2_title = level2_title
            continue

        if not current_lines:
            current_lines = [line]
            current_start_line = idx
            current_title = None
            current_level1_title = level1_title
            current_level2_title = level2_title
            continue

        current_text = "\n".join(current_lines)

        if len(current_text) + len(line) + 1 > max_chars:
            previous_title = current_title
            previous_l1 = current_level1_title
            previous_l2 = current_level2_title

            flush(end_line=idx - 1)

            if previous_title:
                current_lines = [previous_title, line]
            else:
                current_lines = [line]

            current_start_line = idx
            current_title = previous_title
            current_level1_title = previous_l1
            current_level2_title = previous_l2
        else:
            current_lines.append(line)

    flush(end_line=len(lines) - 1)

    return sections


# =========================================================
# 11. Embedding 생성
# =========================================================

def build_embedding_content(section: dict) -> str:
    if INCLUDE_TITLE_PATH_IN_CONTENT and section.get("title_path"):
        return f"[{section['title_path']}]\n{section['content']}"

    return section["content"]


def get_embeddings(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    embedding_model = get_model()

    output = embedding_model.encode(
        texts,
        batch_size=EMBEDDING_BATCH_SIZE,
        max_length=8192
    )

    return [vec.tolist() for vec in output["dense_vecs"]]


# =========================================================
# 12. Supabase 저장
# =========================================================

def save_sections_to_supabase(
    category: str,
    file_name: str,
    file_path: str,
    sections: list[dict],
    embeddings: list[list[float]],
):
    rows = []

    for chunk_index, (section, embedding) in enumerate(zip(sections, embeddings)):
        content_for_storage = build_embedding_content(section)

        rows.append({
            "category": category,
            "file_name": file_name,
            "file_path": file_path,
            "chunk_index": chunk_index,
            "content": content_for_storage,
            "embedding": embedding,
            "metadata": {
                "embedding_model": EMBEDDING_MODEL_NAME,
                "embedding_dim": EMBEDDING_DIM,
                "source": "make_chunks.py + section_merge",
                "chunk_unit": "section",
                "root_title": section["root_title"],
                "section_title": section["section_title"],
                "parent_title": section["parent_title"],
                "level1_title": section["level1_title"],
                "level2_title": section["level2_title"],
                "title_path": section["title_path"],
                "start_line": section["start_line"],
                "end_line": section["end_line"],
                "max_chars": MAX_SECTION_CHARS,
                "title_path_in_content": INCLUDE_TITLE_PATH_IN_CONTENT,
            }
        })

    if not rows:
        return

    client = get_supabase()

    for start in range(0, len(rows), SUPABASE_BATCH_SIZE):
        batch = rows[start:start + SUPABASE_BATCH_SIZE]

        client.table("chunks").upsert(
            batch,
            on_conflict="category,file_name,chunk_index"
        ).execute()


# =========================================================
# 13. chunk 파일 수집
# =========================================================

def collect_chunk_files() -> list[tuple[str, Path]]:
    chunk_files = []

    for category in CATEGORIES:
        category_dir = BASE_DIR / category

        if not category_dir.exists():
            print(f"폴더 없음: {category_dir}")
            continue

        for file_path in category_dir.glob("*_chunks.txt"):
            chunk_files.append((category, file_path))

    return chunk_files


# =========================================================
# 14. section 병합 미리보기
# =========================================================

def preview_sections(file_path: Path, limit: int = 20) -> None:
    print(f"[1] 파일 읽기 시작: {file_path}")
    lines = read_and_expand_chunk_lines(file_path)

    print(f"[2] 확장된 줄 수: {len(lines)}")
    sections = merge_lines_into_sections(lines, max_chars=MAX_SECTION_CHARS)

    print(f"[3] section 수: {len(sections)}")

    for i, section in enumerate(sections[:limit]):
        print("=" * 100)
        print(f"[SECTION {i}]")
        print(f"root_title    : {section['root_title']}")
        print(f"title_path    : {section['title_path']}")
        print(f"level1        : {section['level1_title']}")
        print(f"level2        : {section['level2_title']}")
        print(f"section_title : {section['section_title']}")
        print(f"line          : {section['start_line']} ~ {section['end_line']}")
        print("-" * 100)
        print(build_embedding_content(section)[:1000])


# =========================================================
# 15. main
# =========================================================

def main():
    chunk_files = collect_chunk_files()

    print(f"총 {len(chunk_files)}개의 chunk 파일을 찾았습니다.")

    total_sections = 0

    for category, file_path in tqdm(chunk_files):
        lines = read_and_expand_chunk_lines(file_path)

        if not lines:
            print(f"빈 파일 건너뜀: {file_path}")
            continue

        sections = merge_lines_into_sections(lines, max_chars=MAX_SECTION_CHARS)

        if not sections:
            print(f"section 생성 실패: {file_path}")
            continue

        texts = [build_embedding_content(section) for section in sections]
        embeddings = get_embeddings(texts)

        if len(sections) != len(embeddings):
            raise RuntimeError(
                f"section 수와 embedding 수가 다릅니다: "
                f"{file_path}, sections={len(sections)}, embeddings={len(embeddings)}"
            )

        save_sections_to_supabase(
            category=category,
            file_name=file_path.name,
            file_path=str(file_path),
            sections=sections,
            embeddings=embeddings,
        )

        total_sections += len(sections)

        print(
            f"{file_path.name} -> "
            f"확장 줄 수: {len(lines)}, "
            f"section 수: {len(sections)} 저장 완료"
        )

    print(f"전체 section embedding 저장 완료: {total_sections}개")


if __name__ == "__main__":
    # 먼저 미리보기로 확인
    # preview_sections(
    #     Path("preprocessing/results/card/hyundai_card1_2026_chunks.txt"),
    #     limit=30
    # )

    # 실제 DB 저장
    main()