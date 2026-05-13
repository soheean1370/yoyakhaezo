import streamlit as st

st.set_page_config(
    page_title="OX 퀴즈 | 요약해조",
    page_icon="🧩",
    layout="wide",
)

# 세션 확인
if "chunks" not in st.session_state:
    st.warning("먼저 약관 분석을 진행해주세요.")
    if st.button("← 분석 페이지로 이동"):
        st.switch_page("pages/1_약관분석.py")
    st.stop()

chunks = st.session_state.get("chunks", [])
use_rag = st.session_state.get("use_rag", False)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;900&display=swap');

.stApp {
    background:#FFF9F0;
    font-family:'Noto Sans KR',sans-serif;
}

.quiz-card {
    background:#fff;
    border-radius:20px;
    padding:1.4rem 1.8rem;
    margin-bottom:1rem;
    box-shadow:0 2px 12px rgba(0,0,0,0.06);
}

.quiz-num {
    font-size:0.75rem;
    font-weight:700;
    color:#F5B800;
    letter-spacing:2px;
    margin-bottom:0.5rem;
}

.quiz-q {
    color:#222;
    font-size:1.05rem;
    font-weight:500;
    line-height:1.6;
    margin-bottom:0.8rem;
}

.badge-o {
    display:inline-block;
    background:#E8F5E9;
    color:#2E7D32;
    border:2px solid #A5D6A7;
    border-radius:50px;
    padding:0.3rem 1rem;
    font-size:0.95rem;
    font-weight:700;
}

.badge-x {
    display:inline-block;
    background:#FFEBEE;
    color:#C62828;
    border:2px solid #EF9A9A;
    border-radius:50px;
    padding:0.3rem 1rem;
    font-size:0.95rem;
    font-weight:700;
}

.quiz-expl {
    background:#FFF9F0;
    border-radius:12px;
    padding:0.8rem 1rem;
    margin-top:0.8rem;
    color:#666;
    font-size:0.92rem;
    line-height:1.6;
}
</style>
""", unsafe_allow_html=True)

# 헤더
col1, col2 = st.columns([1,8])

with col1:
    if st.button("← 돌아가기"):
        st.switch_page("pages/1_약관분석.py")

with col2:
    st.markdown("""
    <div style="padding:1rem 0">
        <span style="font-size:1.8rem;font-weight:900;color:#F5B800">
            OX 퀴즈
        </span>
        <span style="font-size:1rem;color:#888;margin-left:0.5rem">
            약관 이해도 확인
        </span>
    </div>
    """, unsafe_allow_html=True)

# 퀴즈 생성
with st.spinner("🧠 퀴즈 생성 중..."):
    from llm.summarizer import generate_quiz

    quizzes = generate_quiz(
        chunks if use_rag else [],
        count=5
    )

st.markdown("## 🧩 약관 내용을 얼마나 이해했는지 확인해보세요!")

for i, q in enumerate(quizzes, 1):

    badge = (
        '<span class="badge-o">⭕ O (맞아요!)</span>'
        if q.get("answer")
        else '<span class="badge-x">❌ X (틀렸어요!)</span>'
    )

    st.markdown(f"""
    <div class="quiz-card">
        <div class="quiz-num">QUIZ {i:02d}</div>

        <div class="quiz-q">
            {q.get('question', '')}
        </div>

        <details>
            <summary style="
                color:#F5B800;
                font-size:0.95rem;
                font-weight:700;
                cursor:pointer
            ">
                ▶ 정답 확인하기
            </summary>

            <div style="padding-top:0.8rem">
                {badge}

                <div class="quiz-expl">
                    💡 {q.get('explanation', '')}
                </div>
            </div>
        </details>
    </div>
    """, unsafe_allow_html=True)