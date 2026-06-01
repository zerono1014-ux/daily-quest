import streamlit as st

st.set_page_config(page_title="개인 맞춤형 퀘스트 생성기", page_icon="🎯", layout="centered")

MAIN_CATS = {
    "외국어": "🌍", "운동": "🏋️‍♂️", "독서": "📚", 
    "시사": "📰", "코딩": "💻"
}

SUB_CATS = {
    "외국어": {"영단어": "📝", "리스닝": "🎧", "독해": "📖"},
    "운동": {"웨이트": "💪", "러닝": "🏃‍♂️", "스트레칭": "🧘"},
    "독서": {"인문": "🧠", "경제": "📈", "기술": "🤖"},
    "시사": {"정치": "⚖️", "경제": "💰", "기술트렌드": "🚀", "미국 정세": "🇺🇸", "중국 동향": "🇨🇳", "일본 마켓": "🇯🇵"},
    "코딩": {"파이썬": "🐍", "SQL": "🗄️", "웹 프론트엔드": "🌐"}
}

# 🌟 핵심: 초기 설정이 끝났는지 기억하는 변수 추가
if 'is_setup_complete' not in st.session_state: st.session_state.is_setup_complete = False
if 'page' not in st.session_state: st.session_state.page = 'main_select'
if 'selected_mains' not in st.session_state: st.session_state.selected_mains = set()
if 'selected_subs' not in st.session_state: st.session_state.selected_subs = set()

# =========================================================
# 📍 [화면 0] 메인 대시보드 (설정을 완료한 경우 무조건 여기로 옴)
# =========================================================
if st.session_state.is_setup_complete:
    # 상단 헤더 (제목과 설정 버튼을 나란히 배치)
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("🔥 나의 일일 퀘스트")
    with col2:
        # 설정 버튼을 누르면 초기화하고 다시 세팅 화면으로 보냄
        if st.button("⚙️ 설정", use_container_width=True):
            st.session_state.is_setup_complete = False
            st.session_state.page = 'main_select'
            st.rerun()

    st.markdown("---")
    st.info(f"현재 고정된 목표: {', '.join(st.session_state.selected_subs)}")

    # 👇 향후 추가될 "소분류별 개별 코드"가 들어갈 메인 무대
    for sub in st.session_state.selected_subs:
        st.subheader(f"🔹 {sub} 퀘스트")
        # 임시 플레이스홀더 (나중에 진짜 기능으로 교체할 부분)
        with st.expander(f"{sub} 오늘의 과제 보기", expanded=True):
            st.write(f"여기에 '{sub}'에 맞는 레벨 진단 결과와 매일 해야 할 과제가 뜰 예정입니다.")
            st.checkbox(f"[{sub}] 과제 완료!", key=f"check_{sub}")

# =========================================================
# 📍 [화면 1] 대분류 카테고리 선택 (초기 설정 안 했을 때만 뜸)
# =========================================================
elif st.session_state.page == 'main_select':
    st.title("🎯 대분류 카테고리 선택")
    st.write("원하는 자기계발 분야를 선택하세요. (여러 개 선택 가능)")
    st.markdown("---")

    cols = st.columns(5)
    for idx, (cat_name, icon) in enumerate(MAIN_CATS.items()):
        with cols[idx]:
            is_selected = cat_name in st.session_state.selected_mains
            button_label = f"✅ {cat_name}" if is_selected else f"{icon} {cat_name}"
            
            if st.button(button_label, use_container_width=True, key=f"main_{cat_name}"):
                if is_selected:
                    st.session_state.selected_mains.remove(cat_name)
                else:
                    st.session_state.selected_mains.add(cat_name)
                st.rerun()

    st.markdown("---")
    if st.button("다음 단계로 (소분류 선택) ➡️", type="primary", use_container_width=True):
        if not st.session_state.selected_mains:
            st.error("⚠️ 최소 1개 이상의 대분류를 선택해주세요.")
        else:
            st.session_state.page = 'sub_select'
            st.rerun()

# =========================================================
# 📍 [화면 2] 소분류 세부 종목 선택
# =========================================================
elif st.session_state.page == 'sub_select':
    st.title("🔍 세부 종목(소분류) 선택")
    st.write("앞서 고른 분야의 구체적인 목표를 선택하세요.")
    st.markdown("---")

    for main_cat in st.session_state.selected_mains:
        st.subheader(f"{MAIN_CATS[main_cat]} {main_cat}")
        sub_dict = SUB_CATS[main_cat]
        
        sub_cols = st.columns(len(sub_dict))
        for idx, (sub_name, icon) in enumerate(sub_dict.items()):
            col_idx = idx % 3 if len(sub_dict) > 3 else idx 
            if len(sub_dict) > 3 and idx % 3 == 0:
                sub_cols = st.columns(3)
                
            with sub_cols[col_idx]:
                is_sub_selected = sub_name in st.session_state.selected_subs
                btn_label = f"✅ {sub_name}" if is_sub_selected else f"{icon} {sub_name}"
                
                if st.button(btn_label, use_container_width=True, key=f"sub_{main_cat}_{sub_name}"):
                    if is_sub_selected:
                        st.session_state.selected_subs.remove(sub_name)
                    else:
                        st.session_state.selected_subs.add(sub_name)
                    st.rerun()
        st.write("") 

    st.markdown("---")
    if len(st.session_state.selected_subs) >= 10:
        st.warning(f"🚨 [과부하 경고] 총 {len(st.session_state.selected_subs)}개를 고르셨네요! 작심삼일이 될 수 있으니 줄이는 것을 권장합니다.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ 뒤로 가기", use_container_width=True):
            st.session_state.page = 'main_select'
            st.rerun()
    with col2:
        # 🌟 여기가 바뀌었어! 선택을 완료하면 대시보드로 영구 고정시킴
        if st.button("✅ 선택 완료 (대시보드 생성)", type="primary", use_container_width=True):
            if not st.session_state.selected_subs:
                st.error("⚠️ 최소 1개 이상의 세부 종목을 선택해주세요.")
            else:
                st.session_state.is_setup_complete = True # 설정 완료 도장 쾅!
                st.rerun() # 새로고침하면 이제 무조건 [화면 0] 대시보드로 감
