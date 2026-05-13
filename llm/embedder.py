import os
from dotenv import load_dotenv
from supabase import create_client
from FlagEmbedding import BGEM3FlagModel

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
)

model = BGEM3FlagModel("BAAI/bge-m3", use_fp16=False)


def get_embedding(text: str) -> list[float]:
    output = model.encode([text], batch_size=1, max_length=8192)
    return output["dense_vecs"][0].tolist()


def search_similar_chunks(
    query: str,
    category: str = None,
    top_k: int = 5,
) -> list[dict]:
    query_vector = get_embedding(query)
    result = supabase.rpc(
        "match_chunks",
        {
            "query_embedding": query_vector,
            "match_count": top_k,
            "filter_category": category,
        }
    ).execute()
    return result.data or []