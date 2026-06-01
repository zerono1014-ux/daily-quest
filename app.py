# ==========================================
# 설치 필요: pip install streamlit google-generativeai
# 실행 방법: streamlit run app.py
# ==========================================

import streamlit as st
import google.generativeai as genai
import json
import datetime
import io

# 1. 앱 기본 설정 (모바일 최적화 레이아웃 주입)
st.set_page_config(page_title="AI 맞춤형 퀘스트 생성기", page_icon="🎯", layout="centered")

st.markdown("""
    <style>
    .main .block-container { padding-top: 1.5rem; padding-bottom: 1.5rem; max-width: 500px; }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: bold; height: 3.2rem; margin-bottom: 0.5rem; }
    .quest-card { background-color: #f8f9fa; padding: 15px; border-radius: 12px; border-left: 5px solid #4a90e2; margin-bottom: 15px; }
    .lock-card { background-color: #fff3cd; padding: 15px; border-radius: 12px; border-left: 5px solid #ffc107; margin-bottom: 15px; color: #856404; }
    </style>
""", unsafe_allow_html=True)

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

# 3. 한국 시간(KST) 계산 함수
def get_kst_now():
    return datetime.datetime.utcnow() + datetime.timedelta(hours=9)

# 4. 세션 상태(State) 초기화 및 확장
if 'is_setup_complete' not in st.session_state: st.session_state.is_setup_complete = False
if 'page' not in st.session_state: st.session_state.page = 'main_select'
if 'selected_mains' not in st.session_state: st.session_state.selected_mains = set()
if 'selected_subs' not in st.session_state: st.session_state.selected_subs = set()

# 🌟 업데이트: 소분야별 개별 주기를 관리할 딕셔너리 세션 생성
if 'quest_cycles' not in st.session_state: st.session_state.quest_cycles = {}

# 영단어 시간차 분리 시스템용 세션
if 'vocab_data_store' not in st.session_state: st.session_state.vocab_data_store = {}
if 'vocab_download_time' not in st.session_state: st.session_state.vocab_download_time = {}
if 'vocab_bypass' not in st.session_state: st.session_state.vocab_bypass = {}

# 시사 리포트 저장용 세션
if 'news_data_store' not in st.session_state: st.session_state.news_data_store = {}

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
# 🧠 AI 생성 로직 함수들 (복기한 프롬프트 정밀 고도화)
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
    # 📌 복기 반영: 토익(TOEIC) 필수 어휘 및 IT/전자공학 실무 기술 전문 용어(Technical Terms) 중심 타겟팅
    prompt = f"""
    영어 교육 전문가이자 공학 기술 영어 멘토입니다. 토익(TOEIC) 필수 고득점 어휘와 IT·전자공학 분야의 기술 전문 용어(Technical Terms)가 혼합된 {level} 수준의 필수 영단어 5개와 이를 완벽히 외웠는지 검증할 미니 퀴즈 3문항을 생성하세요. 
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
    # 📌 복기 반영: 일반 뉴스를 배제하고 AI, 반도체, 대형 테크주(MS, Alphabet, Netflix 등)와 이란-미국 갈등 같은 지정학적 리스크 분석 매칭
    prompt = f"""
    글로벌 금융 및 빅테크 테크 수석 분석가입니다. '{sub}' 분야 및 거시경제 지표와 관련하여, 특히 인공지능(AI), 반도체, 미국 대형 테크주(Microsoft, Alphabet, Netflix)의 최신 핵심 이슈와 이란-미국 전쟁 상황 등 지정학적 리스크가 유가 및 글로벌 공급망에 미치는 나비효과를 집중 분석한 최고급 VIP 브리핑 리포트를 작성하세요.
    반드시 JSON 형식으로 답변:
    {{"headline": "헤드라인", "executive_summary": "3줄 요약", "deep_dive": "심층 배경지식 및 나비효과 분석", "future_impact": "향후 시장 파급 효과"}}
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
    # 📌 복기 반영: <새내기 파이썬> 진도(리스트, 조건문 기본기 등) 연계 및 '개인 주식 포트폴리오 관리 시스템 구축' 프로젝트 확장
    prompt = f"""
    전공 프로그래밍 시니어 멘토입니다. 만약 종목이 '파이썬'인 경우, 교재 <새내기 파이썬>의 진도 범위(리스트 구조 제어, 조건문 논리 설계 등)를 적극 반영하고, 장기적으로 나만의 '개인 주식 포트폴리오 관리 시스템'을 직접 구현하는 데 도움이 되는 연계 미션을 출제해야 합니다. 전공자들이 코드 작성 시 예외를 만들어내거나 실수하기 쉬운 치명적인 '주의할 함정/에러 개념'을 상세히 설명하세요.
    '{sub}' 언어의 '{level}' 수준에 맞춤형 답변을 만드세요.
    반드시 JSON 형식으로 답변:
    {{"title": "미션 제목", "coding_task": "코딩 과제 조건", "trap_concept": "⚠️ 주의할 함정/에러 개념 설명", "mentor_tip": "실무/전공자 팁"}}
    """
    return get_ai_response(prompt)


# ==========================================
# 📍 UI 모듈: 종목별 디스플레이 함수들
# ==========================================
def display_vocab_section(sub):
    st.subheader(f"🌍 {sub} 퀘스트")
    level = st.selectbox(f"{sub} 나의 수준", ["초급", "중급", "고급"], key=f"lvl_{sub}")
    
    # 🌟 업데이트: 영단어 파트 '학습장 선발급(다운로드) - 3시간 타임락 - 퀴즈 오픈' 프로세스 구현
    if sub == "영단어":
        if st.button(f"☀️ 1단계: 오늘자 맞춤형 단어장 발급받기", key=f"btn_{sub}_step1"):
            with st.spinner("토익 및 IT 공학 기술 영단어를 취합하여 문서를 구성 중..."):
                data = generate_vocab_quest(level)
                if data:
                    st.session_state.vocab_data_store[sub] = data
                    st.session_state.vocab_download_time[sub] = datetime.datetime.now()
                    st.session_state.vocab_bypass[sub] = False
                    st.rerun()
                    
        if sub in st.session_state.vocab_data_store and st.session_state.vocab_data_store[sub]:
            data = st.session_state.vocab_data_store[sub]
            content = f"=== [{level}] 맞춤형 {sub}장 ===\n\n"
            for w in data['words']: 
                content += f"■ {w['en']} : {w['kr']}\n"
            
            st.markdown("<div class='quest-card'><b>📋 단어장 리스트 미리보기</b></div>", unsafe_allow_html=True)
            st.text(content)
            
            st.download_button("📥 단어장 파일(.txt)로 스마트폰에 저장", data=content, file_name=f"vocab_{sub}.txt", use_container_width=True)
            
            # 시간차 계산 (3시간 = 10800초)
            elapsed = (datetime.datetime.now() - st.session_state.vocab_download_time[sub]).total_seconds()
            remains = 10800 - elapsed
            
            st.write("---")
            if remains > 0 and not st.session_state.vocab_bypass.get(sub, False):
                st.markdown(f"""
                <div class='lock-card'>
                    🔒 <b>암기 시간 보장 (과제 잠금 상태)</b><br>
                    단어를 완벽하게 숙지할 시간이 필요합니다.<br>
                    ⏱️ <b>퀴즈 잠금 해제까지 남은 시간:</b> {int(remains // 3600)}시간 {int((remains % 3600) // 60)}분 예정
                </div>
                """, unsafe_allow_html=True)
                if st.button("🔓 [테스트용] 즉시 암기 완료 (퀴즈 열기)", key=f"bypass_{sub}"):
                    st.session_state.vocab_bypass[sub] = True
                    st.rerun()
            else:
                st.markdown("### 🌙 2단계: 암기 검증 미니 퀴즈")
                for i, q in enumerate(data['quizzes']):
                    st.radio(f"Q{i+1}. {q['question']}", q['options'], key=f"quiz_{sub}_{i}")
    else:
        # 리스닝, 독해 항목은 기존 정체성 유지
        if st.button(f"✨ 이번 주기 {sub} 퀘스트 생성", key=f"btn_{sub}"):
            with st.spinner("AI가 과제를 빌드하고 있습니다..."):
                data = generate_vocab_quest(level)
                if data:
                    content = f"[{level} {sub} 자료]\n\n"
                    for w in data['words']: content += f"- {w['en']} : {w['kr']}\n"
                    st.download_button("💾 자료 다운로드", data=content, file_name=f"vocab_{sub}.txt", use_container_width=True)
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
    
    # 🌟 업데이트: 한국 시간(KST) 오전 8시 기준 타임 릴리즈 잠금장치 반영
    kst_now = get_kst_now()
    is_after_8am = kst_now.hour >= 8
    
    if is_after_8am:
        st.info("📢 오늘자(오전 8시 기준) 최신 경제/빅테크 VIP 리포트가 업데이트되었습니다.")
        if st.button(f"✨ 오늘의 VIP 리포트 발행", type="primary", key=f"btn_news_{sub}"):
            with st.spinner("글로벌 거시 정세 및 주요 테크 자산 정보를 취합 중..."):
                data = generate_premium_news(sub)
                if data:
                    st.session_state.news_data_store[sub] = data
                    st.rerun()
                    
        if sub in st.session_state.news_data_store and st.session_state.news_data_store[sub]:
            data = st.session_state.news_data_store[sub]
            st.markdown(f"## {data['headline']}")
            st.success(f"**[핵심 3줄 요약]**\n{data['executive_summary']}")
            st.markdown("### 🔍 Deep Dive (심층 배경)")
            st.write(data['deep_dive'])
            st.markdown("### 🚀 Future Impact (향후 시장 파급 효과)")
            st.info(data['future_impact'])
            
            # 파일 소장을 원하는 니즈 적극 충족
            report_text = f"=== {data['headline']} ===\n\n[요약]\n{data['executive_summary']}\n\n[Deep Dive]\n{data['deep_dive']}\n\n[Future Impact]\n{data['future_impact']}"
            st.download_button("📥 브리핑 리포트 파일(.txt) 다운로드", data=report_text, file_name=f"VIP_Report_{sub}_{kst_now.strftime('%Y%m%d')}.txt", use_container_width=True)
    else:
        st.warning("⏳ 오늘의 신규 리포트 발행 대기 중입니다. (매일 오전 8시 정각 한국시간 기준 자동 오픈)")

def display_coding_section(sub):
    st.subheader(f"💻 {sub} 역량 퀘스트")
    
    # 1. 레벨 테스트가 없는 경우 (네 원본 설계 로직 100% 보존)
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
# 🚀 메인 앱 흐름 (라우터 구조 그대로 유지)
# ==========================================

# [화면 0] 🌟 나의 대시보드 (설정 완료 후 고정)
if st.session_state.is_setup_complete:
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title(f"🔥 나의 퀘스트 대시보드")
    with col2:
        if st.button("⚙️ 재설정", use_container_width=True):
            st.session_state.is_setup_complete = False
            st.session_state.page = 'main_select'
            st.rerun()
            
    st.markdown("---")
    
    # 🌟 업데이트: 각 서브 분류 카테고리 옆에 개별 설정한 주기가 동적으로 표시되도록 바인딩
    for sub in st.session_state.selected_subs:
        main_cat = SUB_TO_MAIN[sub]
        sub_cycle = st.session_state.quest_cycles.get(sub, 1)
        cycle_text = "매일" if sub_cycle == 1 else f"{sub_cycle}일 주기"
        
        with st.expander(f"📌 {sub} ({main_cat}) — [{cycle_text}]", expanded=False):
            if main_cat == "외국어": display_vocab_section(sub)
            elif main_cat == "운동": display_workout_section(sub)
            elif main_cat == "독서": display_reading_section(sub)
            elif main_cat == "시사": display_affairs_section(sub)
            elif main_cat == "코딩": display_coding_section(sub)
            
            st.markdown("---")
            st.checkbox(f"✅ 이번 주기 '{sub}' 퀘스트 완료!", key=f"done_{sub}")

# [화면 1] 온보딩 1단계: 대분류 선택 (네 원본 파일 그대로 보존)
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

# [화면 2] 온보딩 2단계: 소분류 선택 및 주기(Cycle) 개별 설정 분리 고도화
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
                    if is_sub_sel:
                        st.session_state.selected_subs.remove(sub_name)
                        if sub_name in st.session_state.quest_cycles: 
                            del st.session_state.quest_cycles[sub_name]
                    else:
                        st.session_state.selected_subs.add(sub_name)
                        st.session_state.quest_cycles[sub_name] = 1 # 개별 주기 기본값 1일 할당
                    st.rerun()
                    
    # 작심삼일 경고 로직 원본 유지
    if len(st.session_state.selected_subs) >= 10:
        st.warning("🚨 [과부하 경고] 종목이 너무 많습니다! 조절을 권장합니다.")

    st.markdown("---")
    
    # 🌟 업데이트: 단일 주기가 아닌, 선택한 '소분류 종목별 개별 슬라이더' 동적 렌더링 시스템 구현
    if st.session_state.selected_subs:
        st.subheader("⏱️ 소분야 종목별 개별 퀘스트 주기 설정")
        for sub_item in st.session_state.selected_subs:
            st.session_state.quest_cycles[sub_item] = st.slider(
                f"'{sub_item}' 과제는 며칠마다 갱신하시겠습니까?", 
                min_value=1, max_value=7, value=st.session_state.quest_cycles.get(sub_item, 1),
                key=f"cycle_slider_{sub_item}",
                help="1로 설정하면 매일 아침 리셋되는 '일일 퀘스트' 형태가 됩니다."
            )

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
