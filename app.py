# ==========================================
# 설치 필요: pip install streamlit google-generativeai
# 실행 방법: streamlit run app.py
# ==========================================

import streamlit as st
import google.generativeai as genai
import json

# 1. 앱 기본 설정
st.set_page_config(page_title="AI 맞춤형 퀘스트 생성기", page_icon="🎯", layout="centered")

# 2. 데이터베이스 (카테고리 및 아이콘)
MAIN_CATS = {
    "외국어": "🌍", "운동": "🏋️‍♂️", "독서": "📚", 
    "시사": "📰", "코딩": "💻"
}
SUB_CATS = {
    "외국어": {"영단어": "📝", "리스닝": "🎧", "독해": "📖"},
    "운동": {"웨이트": "💪", "러닝": "🏃‍♂️", "스트레칭": "🧘"},
    "독서": {"인문": "🧠", "경제": "📈", "기술": "🤖"},
    "시사": {"정치": "⚖️", "경제": "💰", "기술트렌드": "🚀", "미국 정세": "🇺🇸", "중국 동향": "🇨🇳", "일본 마켓": "🇯🇵"},
    "코딩": {"파이썬": "🐍", "C": "🔵", "Java": "☕"}
}

# 역방향 검색용 (sub -> main 찾기)
SUB_TO_MAIN = {sub: main for main, subs in SUB_CATS.items() for sub in subs}

# 3. 세션 상태(State) 초기화
if 'is_setup_complete' not in st.session_state: st.session_state.is_setup_complete = False
if 'page' not in st.session_state: st.session_state.page = 'main_select'
if 'selected_mains' not in st.session_state: st.session_state.selected_mains = set()
if 'selected_subs' not in st.session_state: st.session_state.selected_subs = set()
if 'quest_cycle' not in st.session_state: st.session_state.quest_cycle = 1  # 기본 1일(매일)

# 코딩 파트 전용 세션 변수
if 'coding_test_questions' not in st.session_state: st.session_state.coding_test_questions = {}
if 'current_q_idx' not in st.session_state: st.session_state.current_q_idx = {}
if 'total_score' not in st.session_state: st.session_state.total_score = {}
if 'coding_level' not in st.session_state: st.session_state.coding_level = {}


# ==========================================
# 🔑 공통 모듈: 사이드바 AI 설정
# ==========================================
with st.sidebar:
    st.header("⚙️ AI 멘토 설정")
    api_key = st.text_input("Gemini API Key를 입력하세요", type="password")
    if api_key:
        genai.configure(api_key=api_key)
        st.success("API 연결 완료!")
    else:
        st.warning("퀘스트를 생성하려면 API 키가 필요합니다.")
    st.markdown("---")
    st.caption("제작: 멋진 AI 퀘스트 기획자")


# ==========================================
# 🧠 AI 생성 로직 함수들 (프롬프트 모듈)
# ==========================================
def get_ai_response(prompt):
    if not api_key: return None
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        clean_text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(clean_text)
    except Exception as e:
        st.error(f"AI 오류: {e}")
        return None

def generate_vocab_quest(level):
    prompt = f"""
    영어 교육 전문가입니다. {level} 수준의 영단어 5개와 미니 퀴즈를 생성하세요. 
    반드시 JSON 형식으로 답변:
    {{"words": [{{"en": "단어", "kr": "뜻"}}], "quizzes": [{{"question": "질문(한영/영한 믹스)", "options": ["보기1","보기2","보기3","보기4"], "answer": "정답"}}]}}
    """
    return get_ai_response(prompt)

def generate_workout_quest(sub, level, location):
    prompt = f"""
    베테랑 트레이너입니다. 종목:{sub}, 수준:{level}, 장소:{location}에 맞는 운동 루틴을 생성하세요. 
    (집인 경우 절대 기구 추가 없이 맨몸운동만 구성)
    반드시 JSON 형식으로 답변:
    {{"routine_title": "루틴 이름", "exercises": [{{"name": "운동명", "specs": "세트/횟수", "tip": "팁"}}], "coach_comment": "격려 한마디"}}
    """
    return get_ai_response(prompt)

def generate_reading_quest(sub, level):
    prompt = f"""
    문해력 전문가입니다. {sub} 분야, {level} 난이도의 지문과 과제를 생성하세요.
    반드시 JSON 형식으로 답변:
    {{"title": "지문 제목", "passage": "본문", "quest_instruction": "과제", "model_answer": "모범 답안"}}
    """
    return get_ai_response(prompt)

def recommend_book_quest(sub, level):
    prompt = f"""
    도서 큐레이터입니다. {sub} 분야, {level} 수준에 맞는 최고의 책 1권을 추천하세요.
    반드시 JSON 형식으로 답변:
    {{"book_title": "책 제목", "author": "저자", "difficulty_reason": "추천 이유", "summary": "3줄 요약", "action_plan": "완독 후 적용할 퀘스트"}}
    """
    return get_ai_response(prompt)

def generate_premium_news(sub):
    prompt = f"""
    수석 분석가입니다. {sub} 분야의 가장 트렌디한 핵심 이슈 1개를 VIP 리포트 형식으로 작성하세요. (수준 무관)
    반드시 JSON 형식으로 답변:
    {{"headline": "헤드라인", "executive_summary": "3줄 요약", "deep_dive": "심층 배경지식", "future_impact": "향후 파급 효과"}}
    """
    return get_ai_response(prompt)

def get_coding_test_paper(sub):
    prompt = f"""
    컴퓨터공학과 교수입니다. '{sub}' 실력 진단을 위해 갈수록 어려워지는 10문제를 출제하세요. 총점 100점.
    반드시 JSON 형식으로 답변:
    {{"questions": [{{"num": 1, "question": "질문", "options": ["1","2","3","4"], "answer": "정답텍스트", "points": 10}}]}}
    """
    return get_ai_response(prompt)

def generate_daily_coding_quest(sub, level):
    prompt = f"""
    시니어 멘토입니다. '{sub}' 언어의 '{level}' 수준에 맞는 미션과 함정 개념을 설명하세요.
    반드시 JSON 형식으로 답변:
    {{"title": "미션 제목", "coding_task": "코딩 과제 조건", "trap_concept": "⚠️ 주의할 함정/에러 개념 설명", "mentor_tip": "실무 팁"}}
    """
    return get_ai_response(prompt)


# ==========================================
# 📍 UI 모듈: 종목별 디스플레이 함수들
# ==========================================
def display_vocab_section(sub):
    st.subheader(f"🌍 {sub} 퀘스트")
    level = st.selectbox(f"{sub} 나의 수준", ["초급", "중급", "고급"], key=f"lvl_{sub}")
    
    if st.button(f"✨ 이번 주기 {sub} 퀘스트 생성", key=f"btn_{sub}"):
        with st.spinner("AI가 단어장과 퀴즈를 만들고 있습니다..."):
            data = generate_vocab_quest(level)
            if data:
                content = f"[{level} {sub}장]\n\n"
                for w in data['words']: content += f"- {w['en']} : {w['kr']}\n"
                
                st.download_button("💾 단어장 다운로드", data=content, file_name=f"vocab_{sub}.txt", use_container_width=True)
                st.write("### 📝 미니 퀴즈")
                for i, q in enumerate(data['quizzes']):
                    st.radio(f"Q{i+1}. {q['question']}", q['options'], key=f"quiz_{sub}_{i}")

def display_workout_section(sub):
    st.subheader(f"🏋️‍♂️ {sub} 퀘스트")
    level = st.selectbox(f"{sub} 숙련도", ["초급", "중급", "고급"], key=f"lvl_{sub}")
    loc = st.radio("오늘 장소는?", ["집 (맨몸)", "헬스장 (기구)"], key=f"loc_{sub}", horizontal=True)
    
    if st.button(f"✨ AI 트레이너에게 루틴 받기", key=f"btn_{sub}"):
        with st.spinner("맞춤형 루틴 구성 중..."):
            data = generate_workout_quest(sub, level, "집" if "집" in loc else "헬스장")
            if data:
                st.success(f"💪 {data['routine_title']}")
                content = f"=== {data['routine_title']} ===\n"
                for i, ex in enumerate(data['exercises']):
                    st.markdown(f"**{i+1}. {ex['name']}** | `{ex['specs']}` (💡 {ex['tip']})")
                    content += f"{i+1}. {ex['name']} ({ex['specs']}) - {ex['tip']}\n"
                st.info(f"🗣️ 트레이너: {data['coach_comment']}")
                st.download_button("💾 루틴 저장", data=content, file_name=f"workout_{sub}.txt", use_container_width=True)

def display_reading_section(sub):
    st.subheader(f"📖 {sub} 독서 퀘스트")
    level = st.selectbox(f"{sub} 문해력 수준", ["초급", "중급", "고급"], key=f"lvl_{sub}")
    t1, t2 = st.tabs(["📱 지문 읽기", "📚 책 추천받기"])
    
    with t1:
        if st.button(f"✨ AI 지문 생성", key=f"btn_read_{sub}"):
            with st.spinner("지문 집필 중..."):
                data = generate_reading_quest(sub, level)
                if data:
                    st.markdown(f"### 📌 {data['title']}")
                    st.info(data['passage'])
                    st.write(f"📝 미션: {data['quest_instruction']}")
                    st.text_area("내 생각 기록", key=f"note_{sub}")
                    with st.expander("💡 AI 해설 보기"): st.write(data['model_answer'])
    with t2:
        if st.button(f"✨ 맞춤 도서 큐레이션", type="primary", key=f"btn_book_{sub}"):
            with st.spinner("데이터 분석 중..."):
                data = recommend_book_quest(sub, level)
                if data:
                    st.success(f"『{data['book_title']}』 ({data['author']})")
                    st.write(f"**추천 이유:** {data['difficulty_reason']}")
                    st.write(f"**요약:** {data['summary']}")
                    st.warning(f"🎯 퀘스트: {data['action_plan']}")

def display_affairs_section(sub):
    st.subheader(f"📰 {sub} 프리미엄 브리핑")
    if st.button(f"✨ 오늘의 VIP 리포트 발행", type="primary", key=f"btn_news_{sub}"):
        with st.spinner("정보 취합 중..."):
            data = generate_premium_news(sub)
            if data:
                st.markdown(f"## {data['headline']}")
                st.success(f"**[요약]**\n{data['executive_summary']}")
                st.markdown("### 🔍 Deep Dive")
                st.write(data['deep_dive'])
                st.markdown("### 🚀 Future Impact")
                st.info(data['future_impact'])

def display_coding_section(sub):
    st.subheader(f"💻 {sub} 역량 퀘스트")
    
    # 1. 레벨 테스트가 없는 경우
    if sub not in st.session_state.coding_level:
        st.write("📌 실력 진단 테스트(10문항)가 필요합니다.")
        if sub not in st.session_state.coding_test_questions:
            if st.button("📝 레벨 테스트 시작", type="primary", key=f"start_{sub}"):
                with st.spinner("시험지 출제 중..."):
                    paper = get_coding_test_paper(sub)
                    if paper:
                        st.session_state.coding_test_questions[sub] = paper['questions']
                        st.session_state.current_q_idx[sub] = 0
                        st.session_state.total_score[sub] = 0
                        st.rerun()
        else:
            idx = st.session_state.current_q_idx[sub]
            questions = st.session_state.coding_test_questions[sub]
            
            if idx < 10:
                q = questions[idx]
                st.markdown(f"### Q{q['num']}. (배점: {q['points']}점)")
                st.info(q['question'])
                user_ans = st.radio("정답 선택:", q['options'], key=f"q_{sub}_{idx}")
                
                if st.button("다음 문제 ➡️", key=f"next_{sub}_{idx}"):
                    if user_ans == q['answer']: st.session_state.total_score[sub] += q['points']
                    st.session_state.current_q_idx[sub] += 1
                    st.rerun()
            else:
                score = st.session_state.total_score[sub]
                lvl = "고급" if score >= 80 else ("중급" if score >= 40 else "초급")
                st.success(f"테스트 종료! 점수: {score}점 / 판정: {lvl}자")
                if st.button("등급 확정", key=f"conf_{sub}"):
                    st.session_state.coding_level[sub] = lvl
                    st.rerun()
                    
    # 2. 레벨이 고정된 경우 (퀘스트 진행)
    else:
        lvl = st.session_state.coding_level[sub]
        st.write(f"현재 등급: **[{lvl}]**")
        if st.button(f"✨ AI 멘토 미션 받기", type="primary", key=f"daily_{sub}"):
            with st.spinner("과제 추출 중..."):
                data = generate_daily_coding_quest(sub, lvl)
                if data:
                    st.markdown(f"## 🎯 {data['title']}")
                    st.write(f"**과제:** {data['coding_task']}")
                    st.error(f"⚠️ **함정 주의:** {data['trap_concept']}")
                    st.caption(f"💡 멘토: {data['mentor_tip']}")


# ==========================================
# 🚀 메인 앱 흐름 (라우터)
# ==========================================

# [화면 0] 🌟 나의 대시보드 (설정 완료 후 고정)
if st.session_state.is_setup_complete:
    col1, col2 = st.columns([4, 1])
    with col1:
        # 설정한 주기를 제목에 반영
        cycle = st.session_state.quest_cycle
        cycle_text = "일일" if cycle == 1 else f"{cycle}일 주기"
        st.title(f"🔥 나의 {cycle_text} 퀘스트")
    with col2:
        if st.button("⚙️ 재설정", use_container_width=True):
            st.session_state.is_setup_complete = False
            st.session_state.page = 'main_select'
            st.rerun()
            
    st.markdown("---")
    
    # 선택한 소분류들을 매칭되는 함수로 동적 출력
    for sub in st.session_state.selected_subs:
        main_cat = SUB_TO_MAIN[sub]
        with st.expander(f"📌 {sub} ({main_cat})", expanded=False):
            if main_cat == "외국어": display_vocab_section(sub)
            elif main_cat == "운동": display_workout_section(sub)
            elif main_cat == "독서": display_reading_section(sub)
            elif main_cat == "시사": display_affairs_section(sub)
            elif main_cat == "코딩": display_coding_section(sub)
            
            st.markdown("---")
            st.checkbox(f"✅ 이번 주기 '{sub}' 퀘스트 완료!", key=f"done_{sub}")

# [화면 1] 온보딩 1단계: 대분류 선택
elif st.session_state.page == 'main_select':
    st.title("🎯 대분류 카테고리 선택")
    st.write("관심 있는 분야를 모두 골라주세요.")
    
    cols = st.columns(5)
    for idx, (cat_name, icon) in enumerate(MAIN_CATS.items()):
        with cols[idx]:
            is_sel = cat_name in st.session_state.selected_mains
            btn_lbl = f"✅ {cat_name}" if is_sel else f"{icon} {cat_name}"
            if st.button(btn_lbl, use_container_width=True, key=f"m_{cat_name}"):
                st.session_state.selected_mains.remove(cat_name) if is_sel else st.session_state.selected_mains.add(cat_name)
                st.rerun()

    st.markdown("---")
    if st.button("다음 단계로 ➡️", type="primary", use_container_width=True):
        if not st.session_state.selected_mains: st.error("1개 이상 선택해주세요.")
        else:
            st.session_state.page = 'sub_select'
            st.rerun()

# [화면 2] 온보딩 2단계: 소분류 선택 및 주기(Cycle) 설정
elif st.session_state.page == 'sub_select':
    st.title("🔍 세부 종목 및 주기 설정")
    
    # 선택된 카테고리별 소분류 버튼
    for main_cat in st.session_state.selected_mains:
        st.subheader(f"{MAIN_CATS[main_cat]} {main_cat}")
        sub_dict = SUB_CATS[main_cat]
        sub_cols = st.columns(3)
        
        for idx, (sub_name, icon) in enumerate(sub_dict.items()):
            with sub_cols[idx % 3]:
                is_sub_sel = sub_name in st.session_state.selected_subs
                btn_lbl = f"✅ {sub_name}" if is_sub_sel else f"{icon} {sub_name}"
                if st.button(btn_lbl, use_container_width=True, key=f"s_{sub_name}"):
                    st.session_state.selected_subs.remove(sub_name) if is_sub_sel else st.session_state.selected_subs.add(sub_name)
                    st.rerun()
                    
    if len(st.session_state.selected_subs) >= 10:
        st.warning("🚨 [과부하 경고] 종목이 너무 많습니다! 조절을 권장합니다.")

    st.markdown("---")
    
    # 🌟 추가된 기능: 퀘스트 수행 주기 설정 🌟
    st.subheader("⏱️ 퀘스트 주기 설정")
    st.session_state.quest_cycle = st.slider(
        "며칠마다 새로운 퀘스트를 수행하시겠습니까?", 
        min_value=1, max_value=7, value=st.session_state.quest_cycle, 
        help="1로 설정하면 '일일 퀘스트', 3으로 설정하면 '3일 주기 퀘스트'가 됩니다."
    )
    st.info(f"설정 완료 시, 앱은 **[{st.session_state.quest_cycle}일 주기]**로 동작합니다.")

    # 네비게이션
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ 뒤로 가기", use_container_width=True):
            st.session_state.page = 'main_select'
            st.rerun()
    with col2:
        if st.button("✅ 앱 세팅 완료", type="primary", use_container_width=True):
            if not st.session_state.selected_subs: st.error("1개 이상 선택해주세요.")
            else:
                st.session_state.is_setup_complete = True
                st.rerun()
