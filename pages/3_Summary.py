import streamlit as st

st.set_page_config(
    page_title="요약 결과 | 요약해조",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "result" not in st.session_state:
    st.warning("먼저 약관 분석을 진행해주세요.")
    if st.button("분석 페이지로 이동"):
        st.switch_page("pages/1_Analysis.py")
    st.stop()

result = st.session_state.get("result", {})
category = st.session_state.get("category", "")

category_name_map = {
    "card": "카드",
    "deposit": "예적금",
    "insurance": "보험",
}

category_name = category_name_map.get(category, "알 수 없음")


def get_important_sentences(result):
    sentences = result.get("important_sentences", [])
    if sentences:
        return sentences
    summary = result.get("summary", "")
    if summary:
        return [s.strip() for s in summary.split(".") if s.strip()]
    return []


st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;900&display=swap');
.stApp { background:#FFF9F0; font-family:'Noto Sans KR',sans-serif; }
.block-container { padding:2rem 3rem !important; max-width:1100px !important; }
[data-testid="stSidebarNav"] { display:none; }
.page-header { padding:1rem 0 2rem 0; }
.logo-yellow { font-size:2.2rem; font-weight:900; color:#F5B800; letter-spacing:-1px; }
.header-sub { color:#888; font-size:1.1rem; font-weight:600; margin-left:0.8rem; }
.badge { display:inline-block; background:#E0F7F4; color:#00897B; border:2px solid #80CBC4;
    border-radius:50px; padding:0.35rem 1rem; font-weight:700; font-size:0.9rem; margin-bottom:1rem; }
.section-title { font-size:1.15rem; font-weight:800; color:#333; margin:1.8rem 0 0.9rem 0; }
.summary-card { background:#FFF8E1; border-radius:22px; padding:1.8rem 2rem; margin-bottom:1.5rem;
    border:2px solid #FFE082; box-shadow:0 2px 12px rgba(0,0,0,0.06); }
.summary-label { font-size:0.75rem; font-weight:800; letter-spacing:2px; color:#F5B800; margin-bottom:0.8rem; }
.summary-text { color:#444; font-size:1.08rem; line-height:1.9; font-weight:500; }
.highlight-card { background:#fff; border-radius:20px; padding:1.3rem 1.5rem; margin-bottom:0.9rem;
    box-shadow:0 2px 12px rgba(0,0,0,0.06); border-left:6px solid #F5B800; }
.highlight-num { display:inline-block; min-width:2rem; height:2rem; line-height:2rem; text-align:center;
    background:#FFF3CD; color:#F5B800; border-radius:50%; font-weight:900; margin-right:0.7rem; }
.highlight-text { color:#333; font-size:1rem; line-height:1.7; font-weight:500; }
.empty-box { background:#fff; border-radius:18px; padding:1.2rem 1.5rem; color:#aaa;
    text-align:center; box-shadow:0 2px 12px rgba(0,0,0,0.06); }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="page-header">
    <span class="logo-yellow">요약 결과</span>
    <span class="header-sub">핵심 내용과 중요 문장을 한눈에 확인해요</span>
</div>
""", unsafe_allow_html=True)

st.markdown(f'<div><span class="badge">문서 유형: {category_name}</span></div>', unsafe_allow_html=True)

st.markdown('<div class="section-title">🗒️ 핵심 내용 요약</div>', unsafe_allow_html=True)

summary = result.get("summary", "")

if summary:
    st.markdown(f"""
<div class="summary-card">
    <div class="summary-label">SUMMARY</div>
    <div class="summary-text">{summary}</div>
</div>
""", unsafe_allow_html=True)
else:
    st.markdown('<div class="empty-box">요약 결과가 없습니다.</div>', unsafe_allow_html=True)

st.markdown('<div class="section-title">⭐ 꼭 확인해야 할 문장</div>', unsafe_allow_html=True)

important_sentences = get_important_sentences(result)

if important_sentences:
    for idx, sentence in enumerate(important_sentences, start=1):
        st.markdown(f"""
<div class="highlight-card">
    <span class="highlight-num">{idx}</span>
    <span class="highlight-text">{sentence}</span>
</div>
""", unsafe_allow_html=True)
else:
    st.markdown('<div class="empty-box">강조할 중요 문장이 없습니다.</div>', unsafe_allow_html=True)