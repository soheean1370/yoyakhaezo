import streamlit as st

st.set_page_config(
    page_title="행동 가이드 | 요약해조",
    page_icon="✅",
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


def get_default_guide(category):
    if category == "card":
        return [
            "연회비와 전월 실적 조건을 먼저 확인하세요.",
            "할인 또는 적립 혜택이 본인의 소비 패턴과 맞는지 확인하세요.",
            "혜택 제외 업종이나 제외 가맹점이 있는지 확인하세요.",
            "해외 이용 수수료, 현금서비스, 리볼빙 관련 수수료를 확인하세요.",
            "카드 해지 시 연회비 반환 조건을 확인하세요.",
        ]
    if category == "deposit":
        return [
            "기본금리와 우대금리를 구분해서 확인하세요.",
            "우대금리를 받기 위한 조건을 실제로 충족할 수 있는지 확인하세요.",
            "월 납입 한도와 전체 저축 한도를 확인하세요.",
            "중도해지 시 적용되는 금리와 불이익을 확인하세요.",
            "만기일과 자동 재예치 여부를 확인하세요.",
        ]
    if category == "insurance":
        return [
            "보장되는 항목과 보장되지 않는 항목을 구분해서 확인하세요.",
            "면책기간과 감액기간이 있는지 확인하세요.",
            "보험료 납입 기간과 보험 기간을 확인하세요.",
            "해지환급금과 중도 해지 시 불이익을 확인하세요.",
            "기존 보험과 보장 내용이 중복되는지 확인하세요.",
        ]
    return [
        "가입 대상과 가입 조건을 먼저 확인하세요.",
        "혜택이 적용되는 조건과 제외되는 조건을 함께 확인하세요.",
        "수수료, 위약금, 중도해지 불이익을 확인하세요.",
        "가입 기간, 납입 금액, 만기 조건을 확인하세요.",
        "계약 또는 가입 전 주요 내용을 다시 점검하세요.",
    ]


def get_checklist(category):
    common = [
        "상품의 가입 대상에 내가 해당하는가?",
        "가입 기간 또는 계약 기간을 확인했는가?",
        "혜택을 받기 위한 조건을 확인했는가?",
        "수수료나 위약금 등 불이익 조건을 확인했는가?",
        "나에게 불리한 유의사항이나 제외 조건을 확인했는가?",
    ]
    if category == "card":
        return common + [
            "전월 실적 기준을 충족할 수 있는가?",
            "할인 한도와 적립 한도를 확인했는가?",
            "연회비가 혜택 대비 부담스럽지 않은가?",
            "혜택 제외 업종이나 제외 가맹점을 확인했는가?",
        ]
    if category == "deposit":
        return common + [
            "우대금리 조건을 실제로 충족할 수 있는가?",
            "월 납입 한도와 전체 저축 한도를 확인했는가?",
            "만기 전에 해지할 가능성이 있는가?",
            "중도해지 시 받을 수 있는 금리를 확인했는가?",
        ]
    if category == "insurance":
        return common + [
            "보장 범위가 내가 필요한 항목과 맞는가?",
            "보장 제외 항목을 확인했는가?",
            "면책기간 또는 감액기간을 확인했는가?",
            "보험료를 장기간 납입할 수 있는가?",
        ]
    return common


st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;900&display=swap');
.stApp { background:#FFF9F0; font-family:'Noto Sans KR',sans-serif; }
.block-container { padding:2rem 3rem !important; max-width:1100px !important; }
[data-testid="stSidebarNav"] { display:none; }
.page-header { padding:1rem 0 2rem 0; }
.logo-mint { font-size:2.2rem; font-weight:900; color:#00BFA5; letter-spacing:-1px; }
.header-sub { color:#888; font-size:1.1rem; font-weight:600; margin-left:0.8rem; }
.badge { display:inline-block; background:#E0F7F4; color:#00897B; border:2px solid #80CBC4;
    border-radius:50px; padding:0.35rem 1rem; font-weight:700; font-size:0.9rem; margin-bottom:1rem; }
.section-title { font-size:1.15rem; font-weight:800; color:#333; margin:1.8rem 0 0.9rem 0; }
.guide-card { background:#E0F7F4; border-radius:22px; padding:1.6rem 1.9rem; margin-bottom:1rem;
    border:2px solid #80CBC4; box-shadow:0 2px 12px rgba(0,0,0,0.06); }
.guide-label { font-size:0.75rem; font-weight:800; letter-spacing:2px; color:#00897B; margin-bottom:0.8rem; }
.item-row { display:flex; align-items:flex-start; gap:0.6rem; padding:0.45rem 0;
    font-size:1rem; color:#333; line-height:1.6; }
.guide-arrow { color:#00BFA5; font-weight:900; }
.check-guide-text { color:#777; font-size:0.98rem; line-height:1.7; margin-bottom:1.3rem; padding-left:0.2rem; }
div[data-testid="stCheckbox"] { margin-bottom:0.55rem; }
div[data-testid="stCheckbox"] label { font-size:1rem; color:#333; font-weight:600; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="page-header">
    <span class="logo-mint">행동 가이드</span>
    <span class="header-sub">가입 전 확인해야 할 일을 정리해요</span>
</div>
""", unsafe_allow_html=True)

st.markdown(f'<div><span class="badge">문서 유형: {category_name}</span></div>', unsafe_allow_html=True)

st.markdown('<div class="section-title">👉 사용자 행동 추천</div>', unsafe_allow_html=True)

guide_items = result.get("guide", [])
if not guide_items:
    guide_items = get_default_guide(category)

guide_html = ""
for item in guide_items:
    guide_html += f"""
<div class="item-row">
    <span class="guide-arrow">→</span>
    <span>{item}</span>
</div>
"""

st.markdown(f"""
<div class="guide-card">
    <div class="guide-label">ACTION GUIDE</div>
    {guide_html}
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="section-title">✅ 가입 전 체크리스트</div>', unsafe_allow_html=True)

st.markdown("""
<div class="check-guide-text">
    아래 항목을 하나씩 확인하면서 가입 또는 신청 전에 빠뜨린 내용이 없는지 점검해보세요.
</div>
""", unsafe_allow_html=True)

checklist = get_checklist(category)
checked_count = 0

for idx, item in enumerate(checklist, start=1):
    checked = st.checkbox(item, key=f"check_{idx}")
    if checked:
        checked_count += 1

total_count = len(checklist)
progress_value = checked_count / total_count if total_count > 0 else 0

st.progress(progress_value)
st.write(f"체크 완료: {checked_count} / {total_count}")

if checked_count == total_count:
    st.success("모든 항목을 확인했습니다. 가입 전 최종 약관 내용을 한 번 더 확인해보세요.")
elif checked_count >= total_count * 0.7:
    st.info("대부분 확인했습니다. 남은 항목까지 확인하면 더 안전합니다.")
else:
    st.warning("아직 확인하지 않은 항목이 많습니다. 가입 전 주요 조건을 더 확인하는 것이 좋습니다.")