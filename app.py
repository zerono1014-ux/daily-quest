import streamlit as st

# 1. 앱 기본 설정
st.set_page_config(page_title="개인 맞춤형 퀘스트 생성기", page_icon="🎯", layout="centered")

# 2. 데이터베이스 (아이콘 매칭)
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

# 3. 세션 상태(화면 기억) 초기화
if 'page' not in st.session_state: st.session_state.page = 'main_select'
if 'selected_mains' not in st.session_state: st.session_state.selected_mains = set()
if 'selected_subs' not in st.session_state: st.session_state.selected_subs = set()

# =========================================================
# 📍 [화면 1] 대분류 카테고리 선택 (아이콘 버튼 5개 나열)
# =========================================================
if st.session_state.page == 'main_select':
    st.title("🎯 대분류 카테고리 선택")
    st.write("원하는 자기계발 분야를 선택하세요. (여러 개 선택 가능)")
    st.markdown("---")

    # 5개의 열(Column)을 만들어 버튼을 한 줄로 예쁘게 배치
    cols = st.columns(5)
    for idx, (cat_name, icon) in enumerate(MAIN_CATS.items()):
        with cols[idx]:
            # 선택 여부에 따라 버튼 색상(글자) 다르게 표시
            is_selected = cat_name in st.session_state.selected_mains
            button_label = f"✅ {cat_name}" if is_selected else f"{icon} {cat_name}"
            
            # 버튼 클릭 시 토글(Toggle) 로직
            if st.button(button_label, use_container_width=True, key=f"main_{cat_name}"):
                if is_selected:
                    st.session_state.selected_mains.remove(cat_name)
                else:
                    st.session_state.selected_mains.add(cat_name)
                st.rerun() # 화면 새로고침

    st.markdown("---")
    
    # 다음 창으로 넘어가기 버튼
    if st.button("다음 단계로 (소분류 선택) ➡️", type="primary", use_container_width=True):
        if not st.session_state.selected_mains:
            st.error("⚠️ 최소 1개 이상의 대분류를 선택해주세요.")
        else:
            st.session_state.page = 'sub_select'
            st.rerun()

# =========================================================
# 📍 [화면 2] 소분류 세부 종목 선택 (선택한 대분류만 뜸)
# =========================================================
elif st.session_state.page == 'sub_select':
    st.title("🔍 세부 종목(소분류) 선택")
    st.write("앞서 고른 분야의 구체적인 목표를 선택하세요.")
    st.markdown("---")

    # 선택된 대분류들에 대해서만 소분류 버튼 생성
    for main_cat in st.session_state.selected_mains:
        st.subheader(f"{MAIN_CATS[main_cat]} {main_cat}")
        
        sub_dict = SUB_CATS[main_cat]
        # 소분류 개수에 맞춰서 열(Column) 생성
        sub_cols = st.columns(len(sub_dict))
        
        for idx, (sub_name, icon) in enumerate(sub_dict.items()):
            # 열 개수보다 항목이 많으면 줄바꿈 처리를 위해 (예: 시사 카테고리)
            col_idx = idx % 3 if len(sub_dict) > 3 else idx 
            if len(sub_dict) > 3 and idx % 3 == 0:
                sub_cols = st.columns(3) # 3개씩 끊어서 출력
                
            with sub_cols[col_idx]:
                is_sub_selected = sub_name in st.session_state.selected_subs
                btn_label = f"✅ {sub_name}" if is_sub_selected else f"{icon} {sub_name}"
                
                if st.button(btn_label, use_container_width=True, key=f"sub_{main_cat}_{sub_name}"):
                    if is_sub_selected:
                        st.session_state.selected_subs.remove(sub_name)
                    else:
                        st.session_state.selected_subs.add(sub_name)
                    st.rerun()
        st.write("") # 간격 띄우기

    st.markdown("---")
    
    # 🌟 10개 이상 선택 시 경고 메시지 실시간 출력 (진행은 막지 않음)
    if len(st.session_state.selected_subs) >= 10:
        st.warning(f"🚨 [과부하 경고] 총 {len(st.session_state.selected_subs)}개를 고르셨네요! 작심삼일이 될 수 있으니 개수를 줄이는 것을 권장합니다.")

    # 하단 네비게이션 버튼 (이전 / 다음)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ 뒤로 가기", use_container_width=True):
            st.session_state.page = 'main_select'
            st.rerun()
    with col2:
        if st.button("선택 완료 (세부 설정으로 이동) ➡️", type="primary", use_container_width=True):
            if not st.session_state.selected_subs:
                st.error("⚠️ 최소 1개 이상의 세부 종목을 선택해주세요.")
            else:
                st.session_state.page = 'feature_setup'
                st.rerun()

# =========================================================
# 📍 [화면 3] 종목별 세부 기능 및 레벨 테스트 (미래를 위한 뼈대)
# =========================================================
elif st.session_state.page == 'feature_setup':
    st.title("⚙️ 종목별 맞춤 설정 및 퀘스트")
    st.success(f"총 {len(st.session_state.selected_subs)}개의 종목이 선택되었습니다!")
    st.markdown("---")

    # 👇 향후 네가 나한테 요구할 "소분류 항목별 코드"가 이 아래에 쏙쏙 들어갈 예정이야!
    for sub in st.session_state.selected_subs:
        st.subheader(f"🔹 {sub} 설정")
        st.info("이곳에 각 종목별 맞춤형 진단 로직이나 설정 코드가 들어갈 예정입니다.")
        # ex: if sub == '영단어': 
        #         단어 테스트 로직 실행...
        
    st.markdown("---")
    if st.button("⬅️ 다시 선택하기"):
        st.session_state.page = 'sub_select'
        st.rerun()
