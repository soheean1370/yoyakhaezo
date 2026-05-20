import os
import numpy as np
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

DUMMY_MODE = False

# 로컬 임베딩 모델 (무료, 90MB)
embed_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

# OpenAI gpt-4o-mini (저렴)
llm = ChatOpenAI(
    model="gpt-4o-mini",
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0.3,
    max_tokens=1000,
)

SUMMARY_PROMPT = PromptTemplate(
    input_variables=["text"],
    template="""
당신은 금융 약관 분석 전문가입니다.
아래 금융 약관을 읽고 반드시 아래 형식으로 분석해주세요.
내용이 없으면 "없음"이라고 쓰세요.

[핵심요약]
(3줄 이내로 이 약관의 핵심을 요약)

[혜택]
- (혜택 항목 1)
- (혜택 항목 2)

[주의사항]
- (주의사항 항목 1)
- (주의사항 항목 2)

[조건]
- (조건 항목 1)

[행동가이드]
- (사용자가 실제로 해야 할 행동 1)
- (사용자가 실제로 해야 할 행동 2)

===약관 내용===
{text}
""",
)

QUIZ_PROMPT = PromptTemplate(
    input_variables=["text", "count"],
    template="""
다음 금융 약관 내용을 읽고 OX 퀴즈 {count}개를 만들어주세요.
참/거짓을 반반 섞어서 실제 내용 기반으로 만드세요.

[퀴즈1]
질문: (질문 내용)
정답: O 또는 X
해설: (설명)

[퀴즈2]
질문: (질문 내용)
정답: O 또는 X
해설: (설명)

[퀴즈3]
질문: (질문 내용)
정답: O 또는 X
해설: (설명)

===약관 내용===
{text}
""",
)

summary_chain = SUMMARY_PROMPT | llm | StrOutputParser()
quiz_chain    = QUIZ_PROMPT    | llm | StrOutputParser()


def chunk_text(text: str, max_chars: int = 500) -> list[str]:
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    chunks = []
    current = ""

    for line in lines:
        if len(current) + len(line) + 1 > max_chars:
            if current:
                chunks.append(current.strip())
            current = line
        else:
            current = current + "\n" + line if current else line

    if current:
        chunks.append(current.strip())

    return chunks


def search_relevant_chunks(text: str, query: str, top_k: int = 5) -> str:
    chunks = chunk_text(text)
    print(f"[RAG] 전체 청크 수: {len(chunks)}")

    if not chunks:
        return text[:2000]

    chunk_embeddings = embed_model.encode(chunks)
    query_embedding  = embed_model.encode([query])[0]

    scores = np.dot(chunk_embeddings, query_embedding) / (
        np.linalg.norm(chunk_embeddings, axis=1) * np.linalg.norm(query_embedding) + 1e-9
    )

    top_indices = np.argsort(scores)[::-1][:top_k]
    top_chunks  = [chunks[i] for i in sorted(top_indices)]

    context = "\n\n".join(top_chunks)
    print(f"[RAG] 선택된 청크: {len(top_chunks)}개 / 컨텍스트 길이: {len(context)}자")
    return context


def summarize(text: str, category: str = None) -> dict:
    print(f"\n[요약] 시작 - 전체 텍스트 길이: {len(text)}자")

    if DUMMY_MODE:
        return {
            "summary"   : "이 약관은 카드 연회비, 혜택, 주의사항 등 주요 내용을 담고 있습니다.",
            "benefits"  : ["국내외 가맹점 포인트 적립", "커피 브랜드 추가 적립"],
            "cautions"  : ["연회비 선청구", "전월 실적 기준 충족 필요"],
            "conditions": ["전월 이용금액 20만원 이상"],
            "guide"     : ["전월 실적 매월 확인하기", "연회비 청구일 확인하기"],
            "raw"       : "더미 데이터"
        }

    query   = "핵심 혜택 주의사항 조건 연회비 금리 보험료"
    context = search_relevant_chunks(text, query, top_k=5)
    print(f"[요약] OpenAI 호출 중...")
    raw     = summary_chain.invoke({"text": context})
    print(f"[요약] 완료!")
    return _parse_summary(raw)


def generate_quiz(text: str, count: int = 5, category: str = None) -> list[dict]:
    print(f"\n[퀴즈] 시작")

    if DUMMY_MODE:
        return [
            {"question": "연회비는 카드 발급 시 먼저 청구된다.", "answer": True,  "explanation": "연회비는 발급 시 선청구됩니다."},
            {"question": "전월 실적과 관계없이 포인트가 적립된다.", "answer": False, "explanation": "전월 실적 기준을 충족해야 합니다."},
            {"question": "해지 시 남은 연회비는 일할 계산하여 반환된다.", "answer": True, "explanation": "잔여일수 기준으로 반환됩니다."},
        ]

    query   = "주요 내용 규정 조건 제한 혜택 금액"
    context = search_relevant_chunks(text, query, top_k=5)
    print(f"[퀴즈] OpenAI 호출 중...")
    raw     = quiz_chain.invoke({"text": context, "count": str(count)})
    print(f"[퀴즈] 완료!")
    return _parse_quiz(raw)


def _parse_summary(raw: str) -> dict:
    result = {
        "summary"   : "",
        "benefits"  : [],
        "cautions"  : [],
        "conditions": [],
        "guide"     : [],
        "raw"       : raw,
    }

    section_map = {
        "[핵심요약]" : "summary",
        "[혜택]"     : "benefits",
        "[주의사항]" : "cautions",
        "[조건]"     : "conditions",
        "[행동가이드]": "guide",
    }

    current_section = None
    for line in raw.split("\n"):
        line = line.strip()
        if not line:
            continue

        matched = False
        for header, key in section_map.items():
            if header in line:
                current_section = key
                matched = True
                break

        if matched:
            continue

        if current_section == "summary":
            result["summary"] += (" " + line if result["summary"] else line)
        elif current_section in ["benefits", "cautions", "conditions", "guide"]:
            if line.startswith("- ") or line.startswith("· "):
                item = line[2:].strip()
                if item and item != "없음":
                    result[current_section].append(item)

    return result


def _parse_quiz(raw: str) -> list[dict]:
    quizzes = []
    current = {}

    for line in raw.split("\n"):
        line = line.strip()
        if not line:
            continue

        if line.startswith("[퀴즈") and "]" in line:
            if current.get("question"):
                quizzes.append(current)
            current = {}
        elif line.startswith("질문:"):
            current["question"] = line.replace("질문:", "").strip()
        elif line.startswith("정답:"):
            current["answer"] = line.replace("정답:", "").strip().upper() == "O"
        elif line.startswith("해설:"):
            current["explanation"] = line.replace("해설:", "").strip()

    if current.get("question"):
        quizzes.append(current)

    return quizzes