import streamlit as st
import google.generativeai as genai
import datetime
import io

# ==========================================
# 1. 페이지 설정 및 모바일 최적화 UI
# ==========================================
st.set_page_config(page_title="Daily Quest Master v3", page_icon="🔥", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .main .block-container { padding-top: 1.5rem; padding-bottom: 1.5rem; max-width: 500px; }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: bold; height: 3.2rem; margin-bottom: 0.5rem; }
    .quest-card { background-color: #f8f9fa; padding: 15px; border-radius: 12px; border-left: 5px solid #4a90e2; margin-bottom: 15px; }
    .lock-card { background-color: #fff3cd; padding: 15px; border-radius: 12px; border-left: 5px solid #ffc107; margin-bottom: 15px; color: #856404; }
    .warn-card { background-color: #f8d7da; padding: 15px; border-radius: 12px; border-left: 5px solid #dc3545; margin-bottom: 15px; color: #721c24; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 초기화 및 유틸리티 함수
# ==========================================
if "api_key" in st.secrets:
    genai.configure(api_key=st.secrets["api_key"])
elif "api_key" in st.session_state and st.session_state.api_key:
    genai.configure(api_key=st.session_state.api_key)

def get_kst_now():
    return datetime.datetime.utcnow() + datetime.timedelta(hours=9)

# 세션 상태 초기화
if "step" not in st.session_state:
    st.session_state.step = 1 # 1: 카테고리 선택, 2: 세부 설정, 3: 메인 대시보드
if "selected_cats" not in st.session_state:
    st.session_state.selected_cats = []
if "settings" not in st.session_state:
    st.session_state.settings = {}

# 데이터 상태 초기화
if "vocab_data" not in st.session_state: st.session_state.vocab_data = None
if "vocab_time" not in st.session_state: st.session_state.vocab_time = None
if "bypass_lock" not in st.session_state: st.session_state.bypass_lock = False
if "news_data" not in st.session_state: st.session_state.news_data = None
if "news_date" not in st.session_state: st.session_state.news_date = None

kst_now = get_kst_now()

# ==========================================
# 3. 화면 라우팅 (온보딩 vs 대시보드)
# ==========================================

# --- [Step 1] 종목 선택 화면 ---
if st.session_state.step == 1:
    st.title("🔥 자기계발 온보딩")
    st.write("앞으로 꾸준히 진행할 퀘스트 종목을 선택하세요.")
    
    cats = ["외국어", "시사", "코딩", "운동", "독서"]
    selected = st.multiselect("관심 분야 선택 (여러 개 가능)", cats, default=st.session_state.selected_cats)
    
    if len(selected) >= 4:
        st.markdown("<div class='warn-card'>🚨 <b>작심삼일 경고!</b><br>처음부터 너무 많은 목표를 잡으면 지치기 쉽습니다. 3개 이하로 줄이는 것을 강력히 권장합니다.</div>", unsafe_allow_html=True)
        
    if st.button("다음: 세부 주기 설정 ➡️"):
        if not selected:
            st.error("최소 1개 이상의 분야를 선택해주세요.")
        else:
            st.session_state.selected_cats = selected
            for c in selected:
                if c not in st.session_state.settings:
                    st.session_state.settings[c] = {"cycle": "매일"} # 기본값
            st.session_state.step = 2
            st.rerun()

# --- [Step 2] 세부 주기/옵션 설정 화면 ---
elif st.session_state.step == 2:
    st.title("⚙️ 분야별 맞춤 설정")
    st.write("각 분야의 과제 주기와 난이도를 설정합니다.")
    
    for c in st.session_state.selected_cats:
        st.markdown(f"### {c}")
        st.session_state.settings[c]["cycle"] = st.select_slider(
            f"[{c}] 과제 주기", options=["매일", "2일 주기", "3일 주기", "5일 주기", "7일 주기"], 
            value=st.session_state.settings[c].get("cycle", "매일"), key=f"cycle_{c}"
        )
        # 종목별 특화 설정
        if c == "외국어":
            st.session_state.settings[c]["level"] = st.selectbox("영단어 난이도", ["초급", "중급", "고급"], key=f"lvl_{c}")
        elif c == "코딩":
            st.session_state.settings[c]["level"] = st.selectbox("파이썬 난이도", ["기초(문법/리스트/조건문)", "중급(알고리즘)", "고급(설계)"], key=f"lvl_{c}")
        st.write("---")
        
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ 뒤로 가기"):
            st.session_state.step = 1
            st.rerun()
    with col2:
        if st.button("🚀 대시보드 시작하기"):
            st.session_state.step = 3
            st.rerun()

# --- [Step 3] 메인 대시보드 ---
elif st.session_state.step == 3:
    st.title("🔥 나의 퀘스트 대시보드")
    st.caption(f"📅 현재 KST: {kst_now.strftime('%Y-%m-%d %H:%M')}")
    
    if st.button("⚙️ 앱 설정 초기화 (종목 다시 고르기)"):
        st.session_state.step = 1
        st.rerun()
        
    st.write("---")

    # 1. 외국어 (영단어 - 시간차 락 시스템)
    if "외국어" in st.session_state.selected_cats:
        st.markdown(f"### 🌍 외국어 (주기: {st.session_state.settings['외국어']['cycle']})")
        if st.button("☀️ 1단계: 영단어장 파일 다운로드"):
            with st.spinner("단어장 생성 중..."):
                prompt = f"난이도 {st.session_state.settings['외국어'].get('level', '중급')} 필수 영단어 5개 선정. 뜻, 예문 정리."
                try:
                    res = genai.GenerativeModel('gemini-pro').generate_content(prompt)
                    st.session_state.vocab_data = res.text
                    st.session_state.vocab_time = datetime.datetime.now()
                    st.session_state.bypass_lock = False
                except Exception as e: st.error("생성 실패")
                
        if st.session_state.vocab_data:
            vocab_bytes = io.BytesIO(st.session_state.vocab_data.encode('utf-8'))
            st.download_button("📥 영단어장 파일 저장 (.txt)", data=vocab_bytes, file_name="Vocab.txt", mime="text/plain")
            
            # 타이머 로직 (3시간 = 10800초)
            elapsed = (datetime.datetime.now() - st.session_state.vocab_time).total_seconds()
            remains = 10800 - elapsed
            
            if remains > 0 and not st.session_state.bypass_lock:
                st.markdown(f"<div class='lock-card'>🔒 <b>암기 시간 (과제 잠금)</b><br>퀴즈 오픈까지 약 {int(remains//3600)}시간 {int((remains%3600)//60)}분 남음.</div>", unsafe_allow_html=True)
                if st.button("🔓 [테스트용] 즉시 잠금 해제"):
                    st.session_state.bypass_lock = True
                    st.rerun()
            else:
                if st.button("✍️ 2단계: 암기 검증 미니 퀴즈 시작"):
                    with st.spinner("퀴즈 생성 중..."):
                        q_prompt = f"다음 단어로 영한/한영 믹스 퀴즈 3문항 출제. 정답은 밑에 분리.\n{st.session_state.vocab_data}"
                        st.write(genai.GenerativeModel('gemini-pro').generate_content(q_prompt).text)
        st.write("===")

    # 2. 시사 (오전 8시 KST 릴리즈)
    if "시사" in st.session_state.selected_cats:
        st.markdown(f"### 📰 시사 리포트 (주기: {st.session_state.settings['시사']['cycle']})")
        is_after_8am = kst_now.hour >= 8
        
        if is_after_8am:
            st.info("📢 오늘자(오전 8시 기준) 리포트가 준비되었습니다.")
            if st.button("📥 최신 VIP 시사 브리핑 다운로드"):
                with st.spinner("리포트 빌드 중..."):
                    prompt = "오늘자 글로벌 거시경제 지표와 대형 기술주(특히 AI, 반도체), 그리고 중동 지정학적 리스크가 공급망에 미치는 영향을 분석하여 [헤드라인 + 3줄 요약 + 딥다이브 + 향후 파급 효과] 형태의 리포트를 작성해줘."
                    try:
                        res = genai.GenerativeModel('gemini-pro').generate_content(prompt)
                        st.session_state.news_data = res.text
                        st.session_state.news_date = kst_now.strftime('%Y-%m-%d')
                    except: st.error("에러 발생")
            
            if st.session_state.news_data and st.session_state.news_date == kst_now.strftime('%Y-%m-%d'):
                n_bytes = io.BytesIO(st.session_state.news_data.encode('utf-8'))
                st.download_button("📥 브리핑 리포트 저장 (.txt)", data=n_bytes, file_name="News.txt", mime="text/plain")
                with st.expander("미리보기"): st.markdown(st.session_state.news_data)
        else:
            st.warning("⏳ 오늘의 신규 리포트 발행 대기 중입니다. (매일 오전 8시 갱신)")
        st.write("===")

    # 3. 코딩 (전공자 맞춤)
    if "코딩" in st.session_state.selected_cats:
        st.markdown(f"### 💻 코딩 미션 (주기: {st.session_state.settings['코딩']['cycle']})")
        if st.button("🚀 오늘의 파이썬 미션 생성"):
            with st.spinner("코드 생성 중..."):
                prompt = f"난이도 [{st.session_state.settings['코딩'].get('level', '기초')}] 파이썬 미션 1문제. 전자공학 등 시스템 전공자가 프로그래밍 입문 시 자주 헷갈리는 함정 개념(예: 리스트 제어, 조건문 논리)을 하나 짚어 설명해줘."
                try:
                    res = genai.GenerativeModel('gemini-pro').generate_content(prompt)
                    st.markdown("<div class='quest-card'><b>💻 코딩 미션 & 특화 노트</b></div>", unsafe_allow_html=True)
                    st.write(res.text)
                except: st.error("오류 발생")
        st.write("===")

    # 4. 운동 (장소 분기 로직 복구)
    if "운동" in st.session_state.selected_cats:
        st.markdown(f"### 🏋️‍♂️ 운동 루틴 (주기: {st.session_state.settings['운동']['cycle']})")
        place = st.radio("오늘 운동 장소", ["🏠 집 (맨몸/소도구)", "🏢 헬스장 (기구)"], horizontal=True)
        if st.button("💪 오늘 운동 루틴 짜기"):
            with st.spinner("루틴 설계 중..."):
                prompt = f"장소는 '{place}'입니다. 이 환경에 맞는 전신 운동 루틴 3가지를 세트수와 팁과 함께 알려줘."
                try:
                    res = genai.GenerativeModel('gemini-pro').generate_content(prompt)
                    st.markdown("<div class='quest-card'><b>🏋️‍♂️ 맞춤형 운동 루틴</b></div>", unsafe_allow_html=True)
                    st.write(res.text)
                except: st.error("오류 발생")
        st.write("===")

    # 5. 독서 (2가지 탭 분리 복구)
    if "독서" in st.session_state.selected_cats:
        st.markdown(f"### 📚 독서/문해력 (주기: {st.session_state.settings['독서']['cycle']})")
        rtab1, rtab2 = st.tabs(["📖 문해력 트레이닝", "🎯 도서 큐레이션"])
        with rtab1:
            if st.button("🧠 짧은 지문 읽고 질문 답하기"):
                with st.spinner("지문 생성 중..."):
                    prompt = "비문학(과학/경제/철학) 500자 내외 지문 1개와 핵심을 묻는 객관식 1문제, 주관식 1문제를 내줘."
                    st.write(genai.GenerativeModel('gemini-pro').generate_content(prompt).text)
        with rtab2:
            if st.button("🔍 내 상황에 맞는 책 추천받기"):
                with st.spinner("책 찾는 중..."):
                    prompt = "최근 기술 트렌드나 자아성찰에 도움이 되는 책 1권을 추천하고, 3줄 요약과 '실생활 적용 포인트'를 정리해줘."
                    st.write(genai.GenerativeModel('gemini-pro').generate_content(prompt).text)
        st.write("===")
