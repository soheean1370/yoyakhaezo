import streamlit as st
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

st.set_page_config(page_title="OX 퀴즈 | 요약해조", page_icon="🧩", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;900&display=swap');
.stApp { background:#FFF9F0; font-family:'Noto Sans KR',sans-serif; }
.block-container { padding:2rem 3rem !important; max-width:900px !important; }
[data-testid="stSidebarNav"] { display:none; }
.stButton button { background:#F5B800 !important; color:#fff !important;
    border:none !important; border-radius:50px !important; font-weight:700 !important;
    padding:0.75rem 2.5rem !important; font-size:1.05rem !important; }
.question-card { background:#fff; border-radius:20px; padding:2rem;
                 margin-bottom:1.5rem; box-shadow:0 2px 12px rgba(0,0,0,0.06); }
.quiz-num { font-size:0.75rem; font-weight:700; color:#F5B800;
            letter-spacing:2px; margin-bottom:0.8rem; }
.quiz-q { font-size:1.15rem; font-weight:700; color:#222; line-height:1.7; }
.result-card { background:#fff; border-radius:20px; padding:2rem;
               text-align:center; box-shadow:0 2px 12px rgba(0,0,0,0.06); }
.badge-o { display:inline-block; background:#E8F5E9; color:#2E7D32;
           border:2px solid #A5D6A7; border-radius:50px;
           padding:0.4rem 1.2rem; font-size:1rem; font-weight:700; }
.badge-x { display:inline-block; background:#FFEBEE; color:#C62828;
           border:2px solid #EF9A9A; border-radius:50px;
           padding:0.4rem 1.2rem; font-size:1rem; font-weight:700; }
.expl-box { background:#FFF9F0; border-radius:12px; padding:1rem 1.2rem;
            margin-top:1rem; color:#666; font-size:0.95rem; line-height:1.7; }
.score-big { font-size:4rem; font-weight:900; color:#F5B800; line-height:1; }
</style>
""", unsafe_allow_html=True)

# ── 헤더 ─────────────────────────────────────────────────
col_back, col_title = st.columns([1, 8])
with col_back:
    if st.button("← 분석으로"):
        st.switch_page("pages/1_Analysis.py")
with col_title:
    st.markdown("""
    <div style="padding:1rem 0">
        <span style="font-size:1.8rem;font-weight:900;color:#F5B800">요약</span>
        <span style="font-size:1.8rem;font-weight:900;color:#00BFA5">해조</span>
        <span style="color:#888;font-size:1rem;margin-left:0.5rem">OX 퀴즈</span>
    </div>
    """, unsafe_allow_html=True)

# ── session_state 없으면 분석 먼저 ────────────────────────
text = st.session_state.get("text", "")
if not text:
    st.warning("먼저 약관을 분석해주세요!")
    if st.button("📄 분석하러 가기"):
        st.switch_page("pages/1_Analysis.py")
    st.stop()

# ── 퀴즈 생성 (1회만) ─────────────────────────────────────
if "quizzes" not in st.session_state:
    with st.spinner("🧩 퀴즈 만드는 중..."):
        from llm.summarizer import generate_quiz
        st.session_state["quizzes"]       = generate_quiz(text, count=5)
        st.session_state["quiz_index"]    = 0
        st.session_state["quiz_score"]    = 0
        st.session_state["quiz_answers"]  = {}
        st.session_state["quiz_done"]     = False

quizzes    = st.session_state["quizzes"]
idx        = st.session_state["quiz_index"]
score      = st.session_state["quiz_score"]
answers    = st.session_state["quiz_answers"]
total      = len(quizzes)

# ── 결과 화면 ─────────────────────────────────────────────
if st.session_state["quiz_done"]:
    st.balloons()
    pct = int(score / total * 100) if total else 0

    if pct == 100:
        msg, emoji = "완벽해요! 약관을 완전히 이해했어요 🎉", "🏆"
    elif pct >= 60:
        msg, emoji = "잘 하셨어요! 조금만 더 복습해보세요", "👍"
    else:
        msg, emoji = "약관을 다시 한 번 읽어보세요", "📖"

    st.markdown(f"""
    <div class="result-card">
        <div style="font-size:3rem;margin-bottom:1rem">{emoji}</div>
        <div class="score-big">{score} / {total}</div>
        <div style="color:#888;font-size:1.1rem;margin:0.5rem 0 1rem">{msg}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 오답 복습
    wrong = [(i, q) for i, q in enumerate(quizzes) if not answers.get(i, {}).get("correct", False)]
    if wrong:
        st.markdown("### 📝 오답 복습")
        for i, q in wrong:
            user_ans = answers.get(i, {}).get("user_answer", "?")
            correct  = "⭕ O" if q["answer"] else "❌ X"
            st.markdown(f"""
            <div class="question-card">
                <div class="quiz-num">QUIZ {i+1:02d} — 오답</div>
                <div class="quiz-q">{q['question']}</div>
                <div style="margin-top:1rem;display:flex;gap:1rem;align-items:center">
                    <span style="color:#999">내 답: {'⭕ O' if user_ans else '❌ X'}</span>
                    <span>→</span>
                    <span>정답: {correct}</span>
                </div>
                <div class="expl-box">💡 {q.get('explanation','')}</div>
            </div>
            """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 다시 풀기", use_container_width=True):
            for key in ["quizzes", "quiz_index", "quiz_score", "quiz_answers", "quiz_done"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    with col2:
        if st.button("📄 분석으로 돌아가기", use_container_width=True):
            st.switch_page("pages/1_Analysis.py")

    st.stop()

# ── 퀴즈 진행 ─────────────────────────────────────────────
# 진행 바
st.progress((idx) / total)
st.markdown(f"<div style='color:#aaa;font-size:0.9rem;margin-bottom:1rem'>{idx}/{total} 완료</div>",
            unsafe_allow_html=True)

q = quizzes[idx]

st.markdown(f"""
<div class="question-card">
    <div class="quiz-num">QUIZ {idx+1:02d} / {total}</div>
    <div class="quiz-q">{q['question']}</div>
</div>
""", unsafe_allow_html=True)

# 이미 답변한 문항이면 결과 표시
if idx in answers:
    ans    = answers[idx]
    badge  = '<span class="badge-o">⭕ O</span>' if q["answer"] else '<span class="badge-x">❌ X</span>'
    result = "✅ 정답!" if ans["correct"] else "❌ 오답"

    st.markdown(f"""
    <div style="background:#fff;border-radius:20px;padding:1.5rem;box-shadow:0 2px 12px rgba(0,0,0,0.06)">
        <div style="font-size:1.1rem;font-weight:700;margin-bottom:0.8rem">{result}</div>
        <div>정답: {badge}</div>
        <div class="expl-box">💡 {q.get('explanation','')}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if idx + 1 < total:
        if st.button("다음 문제 ▶", use_container_width=True):
            st.session_state["quiz_index"] += 1
            st.rerun()
    else:
        if st.button("🎉 결과 보기", use_container_width=True):
            st.session_state["quiz_done"] = True
            st.rerun()

else:
    # OX 버튼
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⭕", use_container_width=True):
            correct = q["answer"] == True
            st.session_state["quiz_answers"][idx] = {
                "user_answer" : True,
                "correct"     : correct,
            }
            if correct:
                st.session_state["quiz_score"] += 1
            st.rerun()
    with col2:
        if st.button("❌", use_container_width=True):
            correct = q["answer"] == False
            st.session_state["quiz_answers"][idx] = {
                "user_answer" : False,
                "correct"     : correct,
            }
            if correct:
                st.session_state["quiz_score"] += 1
            st.rerun()