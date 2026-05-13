import streamlit as st
import tempfile
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

st.set_page_config(
    page_title="약관 분석 | 요약해조",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;900&display=swap');
.stApp { background:#FFF9F0; font-family:'Noto Sans KR',sans-serif; }
.block-container { padding:2rem 3rem !important; max-width:1100px !important; }
[data-testid="stSidebarNav"] { display:none; }
.stButton button { background:#F5B800 !important; color:#fff !important;
    border:none !important; border-radius:50px !important; font-weight:700 !important;
    padding:0.75rem 2.5rem !important; font-size:1.05rem !important; }
.card { background:#fff; border-radius:20px; padding:1.4rem 1.8rem;
        margin-bottom:1.2rem; box-shadow:0 2px 12px rgba(0,0,0,0.06); }
.summary-card { background:#FFF8E1; border-radius:20px; padding:1.5rem 1.8rem;
                margin-bottom:1.2rem; border:2px solid #FFE082; }
.guide-card { background:#E0F7F4; border-radius:20px; padding:1.5rem 1.8rem;
              margin-bottom:1.2rem; border:2px solid #80CBC4; }
.stat-box { background:#fff; border-radius:20px; padding:1.2rem 1rem;
            text-align:center; box-shadow:0 2px 12px rgba(0,0,0,0.06); }
.stat-val { font-size:2rem; font-weight:900; line-height:1; margin-bottom:0.3rem; }
.stat-lbl { font-size:0.88rem; color:#888; }
.item-row { display:flex; align-items:flex-start; gap:0.6rem; padding:0.35rem 0;
            font-size:1rem; color:#333; line-height:1.6; }
.sec-title { font-size:1.05rem; font-weight:700; color:#444;
             margin:1.5rem 0 0.8rem 0; }
.stTabs [data-baseweb="tab-list"] { background:#fff !important;
    border-radius:50px !important; padding:6px !important;
    box-shadow:0 2px 10px rgba(0,0,0,0.08) !important; width:fit-content !important; }
.stTabs [data-baseweb="tab"] { border-radius:50px !important; font-size:1rem !important;
    font-weight:600 !important; color:#aaa !important; padding:0.5rem 1.5rem !important; }
.stTabs [aria-selected="true"] { background:#F5B800 !important; color:#fff !important; }
.quiz-card { background:#fff; border-radius:20px; padding:1.4rem 1.8rem;
             margin-bottom:1rem; box-shadow:0 2px 12px rgba(0,0,0,0.06); }
.quiz-num { font-size:0.75rem; font-weight:700; color:#F5B800;
            letter-spacing:2px; margin-bottom:0.5rem; }
.quiz-q { color:#222; font-size:1.05rem; font-weight:500;
          line-height:1.6; margin-bottom:0.8rem; }
.badge-o { display:inline-block; background:#E8F5E9; color:#2E7D32;
           border:2px solid #A5D6A7; border-radius:50px;
           padding:0.3rem 1rem; font-size:0.95rem; font-weight:700; }
.badge-x { display:inline-block; background:#FFEBEE; color:#C62828;
           border:2px solid #EF9A9A; border-radius:50px;
           padding:0.3rem 1rem; font-size:0.95rem; font-weight:700; }
.quiz-expl { background:#FFF9F0; border-radius:12px; padding:0.8rem 1rem;
             margin-top:0.8rem; color:#666; font-size:0.92rem; line-height:1.6; }
</style>
""", unsafe_allow_html=True)

# ── 헤더 ─────────────────────────────────────────────────
col_back, col_title = st.columns([1, 8])
with col_back:
    if st.button("← 홈"):
        st.switch_page("app.py")
with col_title:
    st.markdown("""
    <div style="padding:1rem 0">
        <span style="font-size:1.8rem;font-weight:900;color:#F5B800">요약</span>
        <span style="font-size:1.8rem;font-weight:900;color:#00BFA5">해조</span>
        <span style="color:#888;font-size:1rem;margin-left:0.5rem">약관 분석</span>
    </div>
    """, unsafe_allow_html=True)

# ── 카테고리 + 업로드 ─────────────────────────────────────
category_map = {"카드": "card", "예적금": "deposit", "보험": "insurance"}
col1, col2 = st.columns([1, 3])
with col1:
    selected = st.selectbox("약관 종류 선택", list(category_map.keys()))
    category = category_map[selected]

uploaded = st.file_uploader("📄 약관 PDF를 올려주세요", type=["pdf"])

if not uploaded:
    st.markdown("""
    <div style="text-align:center;padding:3rem;color:#ccc">
        <div style="font-size:3rem">📂</div>
        <div style="margin-top:0.5rem">PDF 파일을 업로드하면 AI가 분석해드려요</div>
    </div>
    """, unsafe_allow_html=True)

else:
    file_size_kb = round(uploaded.size / 1024, 1)
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:1rem;background:#fff;
                border-radius:16px;padding:1rem 1.5rem;margin-bottom:1.5rem;
                box-shadow:0 2px 12px rgba(0,0,0,0.06)">
        <span style="font-size:2rem">📄</span>
        <div>
            <div style="color:#222;font-weight:700">{uploaded.name}</div>
            <div style="color:#999;font-size:0.85rem">{file_size_kb} KB</div>
        </div>
        <div style="margin-left:auto">
            <span style="background:#E0F7F4;color:#00897B;border:2px solid #80CBC4;
                         border-radius:50px;padding:0.3rem 1rem;font-weight:700">
                ✓ 업로드 완료
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔍 약관 분석 시작하기"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded.read())
            tmp_path = tmp.name

        try:
            with st.spinner("📄 텍스트 추출 중..."):
                from ocr.pymupdf_ocr import extract_text_pymupdf
                text = extract_text_pymupdf(tmp_path)

            with st.spinner("🗄️ 관련 내용 검색 중..."):
                from llm.embedder import search_similar_chunks
                chunks = search_similar_chunks(
                    query=text[:500],
                    category=category,
                    top_k=10,
                )

            use_rag = bool(chunks)
            if not use_rag:
                st.warning("저장된 관련 청크가 없어 직접 요약합니다.")

            with st.spinner("🧠 AI가 약관을 분석하고 있어요..."):
                from llm.summarizer import summarize_with_rag, summarize_direct, generate_quiz
                result = summarize_with_rag(chunks) if use_rag else summarize_direct(text)

            # 결과를 session_state에 저장 (퀴즈 페이지에서도 사용)
            st.session_state["result"]   = result
            st.session_state["chunks"]   = chunks
            st.session_state["use_rag"]  = use_rag
            st.session_state["category"] = category

            #  통계
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"""
                <div class="stat-box">
                    <div class="stat-val" style="color:#F5B800">{len(chunks)}</div>
                    <div class="stat-lbl">🗄️ 검색된 청크</div>
                </div>""", unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div class="stat-box">
                    <div class="stat-val" style="color:#00BFA5">{len(result['benefits'])}</div>
                    <div class="stat-lbl">✅ 혜택 항목</div>
                </div>""", unsafe_allow_html=True)
            with c3:
                st.markdown(f"""
                <div class="stat-box">
                    <div class="stat-val" style="color:#FF7043">{len(result['cautions'])}</div>
                    <div class="stat-lbl">⚠️ 주의사항 항목</div>
                </div>""", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # ── 탭 ────────────────────────────────────
            st.markdown("## 📋 분석 결과")

            with tab1:
                st.markdown('<div class="sec-title">🗒️ 핵심 요약</div>',
                            unsafe_allow_html=True)
                st.markdown(f"""
                <div class="summary-card">
                    <div style="font-size:0.75rem;font-weight:700;letter-spacing:2px;
                                color:#F5B800;margin-bottom:0.5rem">✨ SUMMARY</div>
                    <div style="color:#444;font-size:1.05rem;line-height:1.8">
                        {result['summary']}
                    </div>
                </div>""", unsafe_allow_html=True)

                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown('<div class="sec-title">✅ 혜택</div>',
                                unsafe_allow_html=True)
                    if result["benefits"]:
                        items = "".join([
                            f'<div class="item-row"><span style="color:#2E7D32">●</span>{b}</div>'
                            for b in result["benefits"]
                        ])
                        st.markdown(
                            f'<div class="card" style="border-top:4px solid #A5D6A7">{items}</div>',
                            unsafe_allow_html=True)

                with c2:
                    st.markdown('<div class="sec-title">⚠️ 주의사항</div>',
                                unsafe_allow_html=True)
                    if result["cautions"]:
                        items = "".join([
                            f'<div class="item-row"><span style="color:#E65100">●</span>{c}</div>'
                            for c in result["cautions"]
                        ])
                        st.markdown(
                            f'<div class="card" style="border-top:4px solid #FFCC80">{items}</div>',
                            unsafe_allow_html=True)

                with c3:
                    st.markdown('<div class="sec-title">📌 조건</div>',
                                unsafe_allow_html=True)
                    if result["conditions"]:
                        items = "".join([
                            f'<div class="item-row"><span style="color:#1565C0">●</span>{c}</div>'
                            for c in result["conditions"]
                        ])
                        st.markdown(
                            f'<div class="card" style="border-top:4px solid #90CAF9">{items}</div>',
                            unsafe_allow_html=True)

                if result["guide"]:
                    st.markdown('<div class="sec-title">👉 꼭 해야 할 것</div>',
                                unsafe_allow_html=True)
                    items = "".join([
                        f'<div class="item-row"><span style="color:#00BFA5;font-weight:700">→</span>{g}</div>'
                        for g in result["guide"]
                    ])
                    st.markdown(f'<div class="guide-card">{items}</div>',
                                unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            col1, col2, col3 = st.columns([1,2,1])

            with col2:
                if st.button("🧩 OX 퀴즈 풀러가기"):
                    st.switch_page("pages/2_OXQUIZ.py")
        except Exception as e:
            st.error(f"오류 발생: {e}")