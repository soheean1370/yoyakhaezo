import streamlit as st
import pandas as pd
from html import escape
import altair as alt

st.set_page_config(
    page_title="혜택 / 주의사항 / 조건 | 요약해조",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------
# 디자인 확인용 더미 데이터
# 실제 분석 연결 후에는 이 if 블록을 삭제하고 아래 세션 확인 코드로 바꾸면 됨
# ---------------------------------------------------------
if "result" not in st.session_state:
    st.session_state["category"] = "card"
    st.session_state["result"] = {
        "summary": "이 카드는 전월 실적 조건을 충족하면 주요 생활 영역에서 할인 혜택을 받을 수 있는 상품입니다.",
        "benefits": [
            "전월 이용금액 조건을 충족하면 생활 영역에서 할인 혜택을 받을 수 있습니다.",
            "온라인 쇼핑, 편의점, 교통 등 자주 사용하는 영역에서 혜택이 제공될 수 있습니다.",
            "일정 조건 충족 시 월 통합 할인 한도 내에서 혜택이 적용됩니다.",
        ],
        "cautions": [
            "전월 실적을 충족하지 못하면 혜택이 제공되지 않을 수 있습니다.",
            "무이자할부, 세금, 상품권 구매 금액은 실적에서 제외될 수 있습니다.",
            "혜택별 월 한도와 제외 업종을 반드시 확인해야 합니다.",
            "일부 가맹점 또는 특정 결제 방식은 혜택 대상에서 제외될 수 있습니다.",
        ],
        "conditions": [
            "전월 이용금액 기준을 충족해야 합니다.",
            "혜택은 월 통합 한도 내에서 적용됩니다.",
            "카드 이용 실적은 약관에서 정한 기준에 따라 산정됩니다.",
            "할인 또는 적립 혜택은 정해진 월 한도 내에서 제공됩니다.",
            "상품 가입 및 이용 조건은 카드사 정책에 따라 변경될 수 있습니다.",
        ],
    }

# 실제 분석 연결 후에는 위의 더미데이터 if 블록을 삭제하고 이 코드를 사용
# if "result" not in st.session_state:
#     st.warning("먼저 약관 분석을 진행해주세요.")
#     if st.button("분석 페이지로 이동"):
#         st.switch_page("pages/1_Analysis.py")
#     st.stop()

result = st.session_state.get("result", {})
category = st.session_state.get("category", "")

category_name_map = {
    "card": "카드",
    "deposit": "예적금",
    "insurance": "보험",
}

category_name = category_name_map.get(category, "알 수 없음")


def get_items(result_data, key):
    value = result_data.get(key, [])

    if value is None:
        return []

    if isinstance(value, list):
        return value

    if isinstance(value, str):
        return [value]

    return []


def make_item_html(items, dot_color):
    html = ""

    for item in items:
        safe_item = escape(str(item))
        html += (
            f'<div class="item-row">'
            f'<span style="color:{dot_color};font-weight:900">●</span>'
            f'<span>{safe_item}</span>'
            f'</div>'
        )

    return html


def make_ratio_item(label, ratio, bg_color, fill_color):
    return (
        f'<div class="ratio-item">'
        f'<div class="ratio-name">{label} '
        f'<span class="ratio-percent">{ratio}%</span></div>'
        f'<div class="ratio-bg" style="background:{bg_color}">'
        f'<div class="ratio-fill" style="width:{ratio}%;background:{fill_color}"></div>'
        f'</div>'
        f'</div>'
    )


benefits = get_items(result, "benefits")
cautions = get_items(result, "cautions")
conditions = get_items(result, "conditions")

# ---------------------------------------------------------
# 컬러
# ---------------------------------------------------------
BENEFIT_DARK = "#2E7D32"
CAUTION_DARK = "#E65100"
CONDITION_DARK = "#1565C0"

# 파스텔톤
BENEFIT_SOFT = "#81C784"
CAUTION_SOFT = "#FFB074"
CONDITION_SOFT = "#64B5F6"

# 연한 배경
BENEFIT_BG = "#E8F5E9"
CAUTION_BG = "#FFF3E0"
CONDITION_BG = "#E3F2FD"

# ---------------------------------------------------------
# CSS
# ---------------------------------------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;900&display=swap');

.stApp {
    background:#FFF9F0;
    font-family:'Noto Sans KR',sans-serif;
}

.block-container {
    padding:2rem 3rem !important;
    max-width:1100px !important;
}

[data-testid="stSidebarNav"] {
    display:none;
}

.page-header {
    padding:1rem 0 2rem 0;
}

.logo-yellow {
    font-size:2.2rem;
    font-weight:900;
    color:#F5B800;
    letter-spacing:-1px;
}

.logo-mint {
    font-size:2.2rem;
    font-weight:900;
    color:#00BFA5;
    letter-spacing:-1px;
}

.header-sub {
    color:#888;
    font-size:1.1rem;
    font-weight:600;
    margin-left:0.8rem;
}

.badge {
    display:inline-block;
    background:#E0F7F4;
    color:#00897B;
    border:2px solid #80CBC4;
    border-radius:50px;
    padding:0.35rem 1rem;
    font-weight:700;
    font-size:0.9rem;
    margin-bottom:1rem;
}

.section-title {
    font-size:1.15rem;
    font-weight:800;
    color:#333;
    margin:1.8rem 0 0.9rem 0;
}

.stat-box {
    background:#fff;
    border-radius:20px;
    padding:1.3rem 1rem;
    text-align:center;
    box-shadow:0 2px 12px rgba(0,0,0,0.06);
}

.stat-val {
    font-size:2.1rem;
    font-weight:900;
    line-height:1;
    margin-bottom:0.4rem;
}

.stat-lbl {
    font-size:0.9rem;
    color:#888;
    font-weight:700;
}

.category-card {
    background:#fff;
    border-radius:22px;
    padding:1.5rem 1.7rem;
    margin-bottom:1rem;
    box-shadow:0 2px 12px rgba(0,0,0,0.06);
}

.card-label {
    font-size:0.75rem;
    font-weight:800;
    letter-spacing:2px;
    margin-bottom:0.8rem;
}

.item-row {
    display:flex;
    align-items:flex-start;
    gap:0.6rem;
    padding:0.45rem 0;
    font-size:1rem;
    color:#333;
    line-height:1.6;
}

.empty-box {
    background:#fff;
    border-radius:18px;
    padding:1.2rem 1.5rem;
    color:#aaa;
    text-align:center;
    box-shadow:0 2px 12px rgba(0,0,0,0.06);
}

/* 시각화 제목 칩 */
.chart-card {
    background:#fff;
    border-radius:50px;
    padding:0.55rem 1.4rem;
    box-shadow:0 2px 10px rgba(0,0,0,0.08);
    margin-bottom:1rem;
    width:fit-content;
    display:flex;
    align-items:center;
    justify-content:center;
}

.chart-title {
    font-weight:600;
    color:#F5B800;
    margin:0;
    font-size:1rem;
}

/* Altair 차트 흰 카드 배경 */
div[data-testid="stAltairChart"] {
    background:#fff;
    border-radius:28px;
    padding:1.2rem 1.4rem 0.8rem 1.4rem;
    box-shadow:0 2px 12px rgba(0,0,0,0.06);
    overflow:hidden;
}

/* RATIO 제목 칩 */
.ratio-card {
    background:#fff;
    border-radius:50px;
    padding:0.55rem 1.4rem;
    box-shadow:0 2px 10px rgba(0,0,0,0.08);
    margin-bottom:1rem;
    width:fit-content;
    display:flex;
    align-items:center;
    justify-content:center;
}

.ratio-label {
    font-size:1rem;
    font-weight:600;
    letter-spacing:1px;
    color:#00BFA5;
    margin:0;
}

/* RATIO 전체 카드 */
.ratio-box {
    background:#fff;
    border-radius:24px;
    padding:1.4rem 1.5rem;
    box-shadow:0 2px 12px rgba(0,0,0,0.05);
}

.ratio-item {
    margin-bottom:1.35rem;
}

.ratio-item:last-child {
    margin-bottom:0;
}

.ratio-name {
    font-weight:700;
    color:#333;
    font-size:1rem;
    margin-bottom:0.45rem;
}

.ratio-percent {
    color:#777;
    font-weight:600;
    margin-left:0.25rem;
}

.ratio-bg {
    width:100%;
    height:13px;
    border-radius:50px;
    overflow:hidden;
}

.ratio-fill {
    height:13px;
    border-radius:50px;
}

/* 탭 스타일 */
.stTabs [data-baseweb="tab-list"] {
    background:#fff !important;
    border-radius:50px !important;
    padding:6px !important;
    box-shadow:0 2px 10px rgba(0,0,0,0.08) !important;
    width:fit-content !important;
    border-bottom:none !important;
}

.stTabs [data-baseweb="tab"] {
    border-radius:50px !important;
    font-size:1rem !important;
    font-weight:700 !important;
    color:#aaa !important;
    padding:0.5rem 1.5rem !important;
}

.stTabs [aria-selected="true"] {
    background:#F5B800 !important;
    color:#fff !important;
}

/* 탭 선택 시 생기는 하단 빨간선 제거 */
.stTabs [data-baseweb="tab-highlight"] {
    display:none !important;
}

/* 탭 아래 회색 구분선 제거 */
.stTabs [data-baseweb="tab-border"] {
    display:none !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# 헤더
# ---------------------------------------------------------
st.markdown(
    """
<div class="page-header">
    <span class="logo-yellow">혜택</span>
    <span class="logo-mint">분류</span>
    <span class="header-sub">혜택, 주의사항, 조건을 한눈에 확인해요</span>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    f"""
<div>
    <span class="badge">문서 유형: {category_name}</span>
</div>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# 통계 카드
# ---------------------------------------------------------
st.markdown('<div class="section-title">📌 카테고리별 요약</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        f"""
<div class="stat-box">
    <div class="stat-val" style="color:{BENEFIT_DARK}">{len(benefits)}</div>
    <div class="stat-lbl">✅ 혜택</div>
</div>
""",
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        f"""
<div class="stat-box">
    <div class="stat-val" style="color:{CAUTION_DARK}">{len(cautions)}</div>
    <div class="stat-lbl">⚠️ 주의사항</div>
</div>
""",
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        f"""
<div class="stat-box">
    <div class="stat-val" style="color:{CONDITION_DARK}">{len(conditions)}</div>
    <div class="stat-lbl">📌 조건</div>
</div>
""",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------
# 카테고리별 정리
# ---------------------------------------------------------
st.markdown('<div class="section-title">📋 카테고리별 정리</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["✅ 혜택", "⚠️ 주의사항", "📌 조건"])

with tab1:
    if benefits:
        items_html = make_item_html(benefits, BENEFIT_DARK)
        st.markdown(
            f"""
<div class="category-card" style="border-top:5px solid #A5D6A7">
    <div class="card-label" style="color:{BENEFIT_DARK}">BENEFITS</div>
    {items_html}
</div>
""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
<div class="empty-box">
    추출된 혜택 항목이 없습니다.
</div>
""",
            unsafe_allow_html=True,
        )

with tab2:
    if cautions:
        items_html = make_item_html(cautions, CAUTION_DARK)
        st.markdown(
            f"""
<div class="category-card" style="border-top:5px solid #FFCC80">
    <div class="card-label" style="color:{CAUTION_DARK}">CAUTIONS</div>
    {items_html}
</div>
""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
<div class="empty-box">
    추출된 주의사항 항목이 없습니다.
</div>
""",
            unsafe_allow_html=True,
        )

with tab3:
    if conditions:
        items_html = make_item_html(conditions, CONDITION_DARK)
        st.markdown(
            f"""
<div class="category-card" style="border-top:5px solid #90CAF9">
    <div class="card-label" style="color:{CONDITION_DARK}">CONDITIONS</div>
    {items_html}
</div>
""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
<div class="empty-box">
    추출된 조건 항목이 없습니다.
</div>
""",
            unsafe_allow_html=True,
        )

# ---------------------------------------------------------
# 시각화 출력
# ---------------------------------------------------------
st.markdown('<div class="section-title">📊 시각화 출력</div>', unsafe_allow_html=True)

chart_df = pd.DataFrame(
    {
        "카테고리": ["혜택", "주의사항", "조건"],
        "항목 수": [len(benefits), len(cautions), len(conditions)],
    }
)

category_order = ["혜택", "주의사항", "조건"]

left_col, right_col = st.columns([1.15, 1])

with left_col:
    st.markdown(
        """
<div class="chart-card">
    <div class="chart-title">Items by Category</div>
</div>
""",
        unsafe_allow_html=True,
    )

    chart = (
        alt.Chart(chart_df)
        .mark_bar(
            cornerRadiusTopLeft=5,
            cornerRadiusTopRight=5,
            cornerRadiusBottomLeft=5,
            cornerRadiusBottomRight=5,
            size=70,
        )
        .encode(
            x=alt.X(
                "카테고리:N",
                sort=category_order,
                axis=alt.Axis(
                    title=None,
                    labelAngle=0,
                    labelFontSize=14,
                    labelColor="#777",
                    labelPadding=12,
                ),
            ),
            y=alt.Y(
                "항목 수:Q",
                axis=alt.Axis(
                    title=None,
                    labelFontSize=12,
                    labelColor="#888",
                    labelPadding=-14,
                    grid=True,
                    gridColor="#F0E7DA",
                    tickCount=4,
                ),
            ),
            color=alt.Color(
                "카테고리:N",
                scale=alt.Scale(
                    domain=["혜택", "주의사항", "조건"],
                    range=[BENEFIT_SOFT, CAUTION_SOFT, CONDITION_SOFT],
                ),
                legend=None,
            ),
            tooltip=["카테고리", "항목 수"],
        )
        .properties(height=310)
        .configure_view(strokeWidth=0)
        .configure_axis(domain=False, ticks=False)
        .configure(background="#FFFFFF")
    )

    st.altair_chart(chart, use_container_width=True)

with right_col:
    total_count = len(benefits) + len(cautions) + len(conditions)

    if total_count == 0:
        benefit_ratio = 0
        caution_ratio = 0
        condition_ratio = 0
    else:
        benefit_ratio = round(len(benefits) / total_count * 100, 1)
        caution_ratio = round(len(cautions) / total_count * 100, 1)
        condition_ratio = round(len(conditions) / total_count * 100, 1)

    st.markdown(
        '<div class="ratio-card">'
        '<div class="ratio-label">RATIO</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    ratio_html = (
        '<div class="ratio-box">'
        + make_ratio_item("✅ 혜택", benefit_ratio, BENEFIT_BG, BENEFIT_SOFT)
        + make_ratio_item("⚠️ 주의사항", caution_ratio, CAUTION_BG, CAUTION_SOFT)
        + make_ratio_item("📌 조건", condition_ratio, CONDITION_BG, CONDITION_SOFT)
        + '</div>'
    )

    st.markdown(ratio_html, unsafe_allow_html=True)

# ---------------------------------------------------------
# 전체 표
# ---------------------------------------------------------
st.markdown('<div class="section-title">🧾 전체 분류 결과</div>', unsafe_allow_html=True)

table_data = []

for item in benefits:
    table_data.append(
        {
            "카테고리": "혜택",
            "내용": item,
        }
    )

for item in cautions:
    table_data.append(
        {
            "카테고리": "주의사항",
            "내용": item,
        }
    )

for item in conditions:
    table_data.append(
        {
            "카테고리": "조건",
            "내용": item,
        }
    )

if table_data:
    result_df = pd.DataFrame(table_data)
    st.dataframe(result_df, use_container_width=True, hide_index=True)
else:
    st.markdown(
        """
<div class="empty-box">
    표시할 분류 결과가 없습니다.
</div>
""",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------
# 페이지 이동 버튼
# ---------------------------------------------------------
st.markdown("<br>", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    if st.button("← 요약 결과 보기"):
        st.switch_page("pages/3_Summary.py")

with col3:
    if st.button("행동 가이드 보기 →"):
        st.switch_page("pages/4_ActionGuide.py")