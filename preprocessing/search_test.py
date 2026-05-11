import os
from pprint import pprint

from dotenv import load_dotenv
from FlagEmbedding import BGEM3FlagModel
from supabase import create_client


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
# 2. Supabase / Embedding Model 설정
# =========================================================

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

model = BGEM3FlagModel(
    "BAAI/bge-m3",
    use_fp16=False
)


# =========================================================
# 3. Embedding 생성
# =========================================================

def get_embedding(text: str) -> list[float]:
    """
    검색 질문을 BAAI/bge-m3 embedding으로 변환한다.
    반환 벡터 차원은 1024.
    """

    output = model.encode(
        [text],
        batch_size=1,
        max_length=8192
    )

    return output["dense_vecs"][0].tolist()


# =========================================================
# 4. Supabase vector search
# =========================================================

def search_chunks(
    query: str,
    category: str | None = None,
    match_count: int = 5
) -> list[dict]:
    """
    질문과 의미적으로 유사한 chunk를 Supabase에서 검색한다.

    category:
    - "card"
    - "deposit"
    - "insurance"
    - None이면 전체 검색
    """

    query_embedding = get_embedding(query)

    response = supabase.rpc(
        "match_chunks",
        {
            "query_embedding": query_embedding,
            "match_count": match_count,
            "filter_category": category
        }
    ).execute()

    return response.data


# =========================================================
# 5. 검색 결과 출력
# =========================================================

def print_results(query: str, results: list[dict]) -> None:
    print("\n" + "=" * 120)
    print(f"검색 질문: {query}")
    print(f"검색 결과 수: {len(results)}")
    print("=" * 120)

    for i, row in enumerate(results, start=1):
        metadata = row.get("metadata") or {}

        print("\n" + "=" * 120)
        print(f"[{i}] similarity: {row.get('similarity')}")
        print(f"category    : {row.get('category')}")
        print(f"file_name   : {row.get('file_name')}")
        print(f"chunk_index : {row.get('chunk_index')}")

        print("-" * 120)
        print("[metadata]")
        print(f"chunk_unit    : {metadata.get('chunk_unit')}")
        print(f"title_path    : {metadata.get('title_path')}")
        print(f"level1_title  : {metadata.get('level1_title')}")
        print(f"level2_title  : {metadata.get('level2_title')}")
        print(f"section_title : {metadata.get('section_title')}")
        print(f"start_line    : {metadata.get('start_line')}")
        print(f"end_line      : {metadata.get('end_line')}")

        print("-" * 120)
        print("[content]")
        print(row.get("content"))


# =========================================================
# 6. main
# =========================================================

def main():
    # 테스트 질문 1: 카드
    # query = "the Orange 카드 연회비는 얼마야?"
    # category = "card"

    # # 2 - 정확하지 않음.
    # query = "공항 라운지 무료 이용 조건은 뭐야?"
    # category = "card"   

    # # # 3
    # query = "중도해지하면 이자는 어떻게 계산돼?"
    # category = "deposit"

    #4
    query = "보험금을 지급하지 않는 경우는 뭐야?"
    category = "insurance"

    results = search_chunks(
        query=query,
        category=category,
        match_count=5
    )

    print_results(query, results)


if __name__ == "__main__":
    main()