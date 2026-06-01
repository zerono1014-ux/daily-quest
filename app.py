import streamlit as st

st.set_page_config(page_title="개인 맞춤형 퀘스트 생성기", page_icon="🎯")

if 'page' not in st.session_state: st.session_state.page = 'select'
if 'selected_subs' not in st.session_state: st.session_state.selected_subs = []
if 'level_results' not in st.session_state: st.session_state.level_results = {}

QUEST_STRUCTURE = {
    "외국어": ["영단어", "리스닝", "독해"], "운동": ["웨이트", "러닝", "스트레칭"],
    "독서": ["인문", "경제", "기술"], "시사": ["정치", "경제", "기술트렌드", "미국 정세", "중국 동향", "일본 마켓"],
    "코딩": ["파이썬", "SQL", "웹 프론트엔드"]
}

if st.session_state.page == 'select':
    st.title("🎯 개인 맞춤형 퀘스트 생성기")
    selected_mains = st.multiselect("대분류 카테고리를 고르세요", list(QUEST_STRUCTURE.keys()))
    if selected_mains:
        selected_subs = []
        for main in selected_mains:
            sub = st.multiselect(f"[{main}] 세부 항목", QUEST_STRUCTURE[main])
            selected_subs.extend(sub)
        if st.button("선택 완료 및 레벨 테스트로 이동 ➡️", use_container_width=True):
            if not selected_subs: st.error("⚠️ 항목을 선택해주세요.")
            elif len(selected_subs) >= 6: st.warning("🚨 6개 이상은 과부하입니다! 줄여주세요.")
            else:
                st.session_state.selected_subs = selected_subs
                st.session_state.page = 'test'
                st.rerun()

elif st.session_state.page == 'test':
    st.title("📊 맞춤형 레벨 진단 테스트")
    current_levels = {}
    for sub in st.session_state.selected_subs:
        choice = st.radio(f"🔹 '{sub}' 실력은 어느 정도인가요?", ["초급", "중급", "고급"], key=f"r_{sub}")
        current_levels[sub] = choice
    if st.button("레벨 진단 완료 (퀘스트 생성) ➡️", type="primary", use_container_width=True):
        st.session_state.level_results = current_levels
        st.success("🎉 레벨 진단 완료! (다음 기능 연동 대기)")
