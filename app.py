import streamlit as st

st.set_page_config(
    page_title="요약해조",
    page_icon="🐟",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;900&display=swap');
.stApp { background:#FFF9F0; font-family:'Noto Sans KR',sans-serif; }
.block-container { padding:2rem 3rem !important; max-width:1100px !important; }
[data-testid="stSidebarNav"] { display:none; }
.hero { text-align:center; padding:4rem 1rem 3rem; }
.hero-logo { font-size:5rem; font-weight:900; letter-spacing:-2px; line-height:1; margin-bottom:1rem; }
.logo-y { color:#F5B800; } .logo-t { color:#00BFA5; }
.hero-sub { color:#888; font-size:1.2rem; margin-bottom:0.5rem; }
.hero-desc { color:#aaa; font-size:0.95rem; margin-bottom:3rem; }
.start-btn { display:inline-block; background:#F5B800; color:#fff;
             font-size:1.2rem; font-weight:700; padding:1rem 3rem;
             border-radius:50px; text-decoration:none;
             box-shadow:0 4px 20px rgba(245,184,0,0.4); }
.feature-card { background:#fff; border-radius:20px; padding:1.5rem;
                text-align:center; box-shadow:0 2px 12px rgba(0,0,0,0.06); }
.feature-icon { font-size:2.5rem; margin-bottom:0.8rem; }
.feature-title { color:#222; font-size:1rem; font-weight:700; margin-bottom:0.3rem; }
.feature-desc { color:#999; font-size:0.85rem; line-height:1.5; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <div class="hero-logo">
        <span class="logo-y">요</span><span class="logo-t">약</span>
        <span class="logo-y">해</span><span class="logo-t">조</span>
    </div>
    <div class="hero-sub">금융 약관, 이제 쉽게 이해하세요 🐟</div>
    <div class="hero-desc">카드 · 보험 · 예적금 약관을 AI가 핵심만 뽑아드려요</div>
</div>
""", unsafe_allow_html=True)

# 시작하기 버튼
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("🔍 약관 분석 시작하기", use_container_width=True):
        st.switch_page("pages/1_Analysis.py")

st.markdown("<br><br>", unsafe_allow_html=True)

# 기능 소개
c1, c2, c3, c4 = st.columns(4)
features = [
    ("📄", "PDF 업로드", "카드·보험·예적금\n약관 PDF 업로드"),
    ("🧠", "AI 분석", "RAG 기반\n핵심 내용 추출"),
    ("✅", "결과 정리", "혜택·주의사항·조건\n한눈에 확인"),
    ("🧩", "OX 퀴즈", "이해도 확인\n게임처럼 즐기기"),
]
for col, (icon, title, desc) in zip([c1, c2, c3, c4], features):
    with col:
        st.markdown(f"""
        <div class="feature-card">
            <div class="feature-icon">{icon}</div>
            <div class="feature-title">{title}</div>
            <div class="feature-desc">{desc}</div>
        </div>
        """, unsafe_allow_html=True)