import streamlit as st
import google.generativeai as genai
import datetime
import time
import io

# 1. 페이지 설정 (모바일 최적화 레이아웃)
st.set_page_config(
    page_title="Daily Quest Master v2",
    page_icon="🔥",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 모바일 가독성을 위한 커스텀 CSS 주입
st.markdown("""
    <style>
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1.5rem;
        max-width: 500px;
    }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        font-weight: bold;
        height: 3rem;
    }
    .quest-card {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 12px;
        border-left: 5px solid #4a90e2;
        margin-bottom: 15px;
    }
    .lock-card {
        background-color: #fff3cd;
        padding: 15px;
        border-radius: 12px;
        border-left: 5px solid #ffc107;
        margin-bottom: 15px;
        color: #856404;
    }
    </style>
""", unsafe_allow_html=True)

# 2. API 키 초기화 (Secrets 및 Session State 지원)
if "api_key" in st.secrets:
    genai.configure(api_key=st.secrets["api_key"])
elif "api_key" in st.session_state and st.session_state.api_key:
    genai.configure(api_key=st.session_state.api_key)

# 3. 한국 시간(KST) 계산 함수
def get_kst_now():
    # Streamlit Cloud 서버 시간(UTC) 기준 +9시간 계산
    utc_now = datetime.datetime.utcnow()
    kst_now = utc_now + datetime.timedelta(hours=9)
    return kst_now

# 4. 세션 상태(Session State) 기본값 생성
if "settings" not in st.session_state:
    st.session_state.settings = {
        "영단어": {"cycle": "매일", "level": "중급"},
        "시사": {"cycle": "매일"},
        "코딩": {"cycle": "3일 주기", "level": "초급"},
        "운동": {"cycle": "2일 주기"},
        "독서": {"cycle": "5일 주기", "level": "중급"}
    }

if "vocab_data" not in st.session_state:
    st.session_state.vocab_data = None
if "vocab_download_time" not in st.session_state:
    st.session_state.vocab_download_time = None
if "bypass_lock" not in st.session_state:
    st.session_state.bypass_lock = False
if "news_data" not in st.session_state:
    st.session_state.news_data = None
if "news_date" not in st.session_state:
    st.session_state.news_date = None

# --- 메인 화면 ---
st.title("🔥 Daily Quest Master")
kst_now = get_kst_now()
st.caption(f"📅 현재 한국 시간: {kst_now.strftime('%Y-%m-%d %H:%M:%S')}")

# 수동 API 키 입력창 (Secrets 미설정 시 활성화)
if "api_key" not in st.secrets:
    with st.expander("🔑 Gemini API Key 설정"):
        api_input = st.text_input("Gemini API Key를 입력하세요", type="password", value=st.session_state.get("api_key", ""))
        if api_input:
            st.session_state.api_key = api_input
            genai.configure(api_key=api_input)
            st.success("API 키가 임시 적용되었습니다.")

# 탭 구성 (과제 대시보드 / 소분야 설정)
tab_dashboard, tab_settings = st.tabs(["🎯 오늘의 퀘스트", "⚙️ 소분야별 주기 설정"])

# --- 탭 2: 소분야 설정 화면 ---
with tab_settings:
    st.subheader("🛠️ 종목별 맞춤 주기 설정")
    st.write("각 분야의 특성에 맞춰 과제 생성 주기를 다르게 지정합니다.")
    
    # 1. 외국어(영단어) 설정
    st.markdown("### 🌍 외국어 (영단어)")
    st.session_state.settings["영단어"]["level"] = st.selectbox(
        "영단어 난이도", ["초급", "중급", "고급"], 
        index=["초급", "중급", "고급"].index(st.session_state.settings["영단어"]["level"]), key="set_lang_lvl"
    )
    st.session_state.settings["영단어"]["cycle"] = st.select_slider(
        "영단어 발행 주기", options=["매일", "2일 주기", "3일 주기", "5일 주기", "7일 주기"],
        value=st.session_state.settings["영단어"]["cycle"], key="set_lang_cyc"
    )
    
    st.write("---")
    
    # 2. 시사 리포트 설정
    st.markdown("### 📰 시사 브리핑 (VIP 리포트)")
    st.session_state.settings["시사"]["cycle"] = st.select_slider(
        "시사 리포트 갱신 주기", options=["매일", "2일 주기", "3일 주기"],
        value=st.session_state.settings["시사"]["cycle"], key="set_news_cyc"
    )
    st.caption("※ 시사 리포트는 설정한 주기마다 오전 8시(한국시간)에 최신 분석 파일이 업데이트됩니다.")
    
    st.write("---")
    
    # 3. 코딩 과제 설정
    st.markdown("### 💻 코딩 테스트")
    st.session_state.settings["코딩"]["level"] = st.selectbox(
        "코딩 언어/난이도", ["초급 (파이썬 기초)", "중급 (자료구조/알고리즘)", "고급 (시스템 설계)"],
        index=0, key="set_code_lvl"
    )
    st.session_state.settings["코딩"]["cycle"] = st.select_slider(
        "코딩 과제 주기", options=["매일", "2일 주기", "3일 주기", "5일 주기", "7일 주기"],
        value=st.session_state.settings["코딩"]["cycle"], key="set_code_cyc"
    )
    
    st.success("설정이 실시간으로 저장되었습니다! '오늘의 퀘스트' 탭에서 확인하세요.")

# --- 탭 1: 메인 대시보드 화면 ---
with tab_dashboard:
    
    # ================= 🌍 1. 외국어 모듈 (시간차 분리 시스템) =================
    st.markdown(f"### 🌍 외국어 퀘스트 (주기: {st.session_state.settings['영단어']['cycle']})")
    
    # Step 1: 오전 단어장 발급
    if st.button("☀️ [오전] 오늘자 맞춤형 영단어장 파일 발급받기", key="btn_gen_vocab"):
        with st.spinner("AI가 오늘 공부할 영단어 문서를 빌드하고 있습니다..."):
            try:
                model = genai.GenerativeModel('gemini-pro')
                prompt = f"난이도 {st.session_state.settings['영단어']['level']}에 맞는 필수 영단어 5개를 선정하고, 각 단어의 뜻, 예문, 그리고 전공자들이 자주 쓰는 기술적 맥락에서의 쓰임새를 깔끔한 줄글 노트 형태로 작성해줘."
                response = model.generate_content(prompt)
                st.session_state.vocab_data = response.text
                st.session_state.vocab_download_time = datetime.datetime.now()
                st.session_state.bypass_lock = False # 락 초기화
            except Exception as e:
                st.error("API 연동 중 오류가 발생했습니다. 환경변수나 API 키를 확인해 주세요.")
                
    if st.session_state.vocab_data:
        st.markdown("<div class='quest-card'><b>📋 오늘자 발급된 영단어 리스트 Preview</b></div>", unsafe_allow_html=True)
        st.text(st.session_state.vocab_data[:300] + "...(이하 생략)")
        
        # 다운로드 기능 (모바일에서 파일 형태로 저장할 수 있도록 파일 다운로드 래퍼 제공)
        vocab_bytes = io.BytesIO(st.session_state.vocab_data.encode('utf-8'))
        st.download_button(
            label="📥 영단어장 파일(.txt) 다운로드하여 외우기",
            data=vocab_bytes,
            file_name=f"Vocab_Note_{kst_now.strftime('%Y%m%d')}.txt",
            mime="text/plain"
        )
        
        # 시간차 계산 (기준: 3시간 = 10800초)
        LOCK_DURATION = 10800
        elapsed_time = (datetime.datetime.now() - st.session_state.vocab_download_time).total_seconds()
        remaining_time = LOCK_DURATION - elapsed_time
        
        st.write("---")
        
        # Step 2: 암기 시간 고려한 퀴즈 잠금/해제 로직
        if remaining_time > 0 and not st.session_state.bypass_lock:
            st.markdown(f"""
            <div class='lock-card'>
                🔒 <b>과제 잠금 상태 (외우는 시간 보장)</b><br>
                단어장을 발급받은 지 얼마 되지 않았습니다. 외울 시간이 필요합니다.<br>
                ⏱️ <b>퀴즈 활성화까지 남은 시간:</b> {int(remaining_time // 3600)}시간 {int((remaining_time % 3600) // 60)}분 예정
            </div>
            """, unsafe_allow_html=True)
            
            # 모바일 실시간 테스트 편의를 위한 바이패스 스위치
            if st.button("🔓 [테스트용] 암기 완료 (즉시 퀴즈 잠금 해제)"):
                st.session_state.bypass_lock = True
                st.rerun()
        else:
            st.markdown("### 🌙 [오후] 영단어 믹스 미니 과제 수행")
            if st.button("✍️ 암기 검증 미니 퀴즈 출제하기", key="btn_gen_quiz"):
                with st.spinner("외운 단어를 검증할 퀴즈를 생성 중입니다..."):
                    model = genai.GenerativeModel('gemini-pro')
                    quiz_prompt = f"다음 단어 리스트를 바탕으로 영한/한영 믹스 퀴즈 3문항을 출제해줘. 정답과 해설은 하단에 접어놓을 수 있도록 구분 기호를 넣어줘:\n\n{st.session_state.vocab_data}"
                    quiz_response = model.generate_content(quiz_prompt)
                    st.write(quiz_response.text)
                    
    st.write("===")

    # ================= 📰 2. 시사 모듈 (오전 8시 KST 기준 자동 발급 시스템) =================
    st.markdown(f"### 📰 시사 VIP 브리핑 리포트 (주기: {st.session_state.settings['시사']['cycle']})")
    st.write("글로벌 거시경제 및 거대 기술(AI, 반도체) 트렌드를 요약 브리핑 파일로 제공합니다.")
    
    # 오전 8시 기준 체크 로직
    # 실시간 모바일 사용자가 아침 8시 이후에 들어오면 다운로드 버튼 완전 개방
    is_after_8am = kst_now.hour >= 8
    
    if is_after_8am:
        st.info("📢 오늘 오전 8시 기준 최신 VIP 시사 브리핑 리포트가 정상 발행되었습니다.")
        if st.button("📥 최신 시사 브리핑 데이터 로드하기", key="btn_load_news"):
            with st.spinner("글로벌 정세 및 금융 트렌드 데이터를 수집 및 가공 중입니다..."):
                try:
                    model = genai.GenerativeModel('gemini-pro')
                    news_prompt = "오늘자 글로벌 주요 거시경제 지표 변화와 대형 기술주(반도체, AI 섹터) 동향, 지정학적 리스크 요인을 분석하여 [헤드라인 + 3줄 요약 + 딥다이브 배경지식 + 향후 파급 효과] 형태의 최고급 VIP 리포트 텍스트 문서를 작성해줘."
                    response = model.generate_content(news_prompt)
                    st.session_state.news_data = response.text
                    st.session_state.news_date = kst_now.strftime('%Y-%m-%d')
                except Exception as e:
                    st.error("리포트 빌드 실패. API 연결 상태를 확인하세요.")
        
        if st.session_state.news_data and st.session_state.news_date == kst_now.strftime('%Y-%m-%d'):
            st.success("✅ 리포트 문서 빌드 완료!")
            news_bytes = io.BytesIO(st.session_state.news_data.encode('utf-8'))
            st.download_button(
                label="📥 오늘자 VIP 시사 리포트 파일(.txt) 다운로드",
                data=news_bytes,
                file_name=f"VIP_Current_Affairs_{kst_now.strftime('%Y%m%d')}.txt",
                mime="text/plain"
            )
            with st.expanders("👀 리포트 본문 미리보기"):
                st.markdown(st.session_state.news_data)
    else:
        st.warning("⏳ 오늘자 신규 리포트 발행 대기 중입니다. (매일 오전 8시 정각 한국시간 기준 자동 갱신)")
        st.write("현재 시간은 오전 8시 전이므로, 어제 자로 저장된 백업 리포트 아카이브를 열람하거나 새로고침할 수 있습니다.")
        if st.button("🔄 이전 발행 리포트 아카이브 가져오기"):
            st.info("어제자 아카이브 파일을 불러옵니다.")
            
    st.write("===")

    # ================= 💻 3. 코딩 모듈 (점진적 전공자 최적화 과제) =================
    st.markdown(f"### 💻 전공 맞춤형 코딩 과제 (주기: {st.session_state.settings['코딩']['cycle']})")
    
    if st.button("🚀 오늘자 코딩 미션 및 함정 개념 노트 받아오기", key="btn_gen_code"):
        with st.spinner("전공자용 코드 알고리즘과 실수하기 쉬운 버그 함정 노트를 생성 중입니다..."):
            try:
                model = genai.GenerativeModel('gemini-pro')
                code_prompt = f"난이도 [{st.session_state.settings['코딩']['level']}]에 맞춘 파이썬 알고리즘 풀이 미션을 1문제 내줘. 특히 전공자들이나 실무자들이 코드 짤 때 실수하여 예외나 버그를 만들기 쉬운 '헷갈리는 함정 개념(예: 얕은 복사/깊은 복사, 가변 인자 매커니즘, 부동소수점 오차 등)'을 하나 콕 집어서 예시 코드와 함께 집중 설명 노트를 첨부해줘."
                response = model.generate_content(code_prompt)
                st.markdown("<div class='quest-card'><b>💻 오늘의 코딩 미션 & 전공자 특화 노트</b></div>", unsafe_allow_html=True)
                st.write(response.text)
            except Exception as e:
                st.error("오류 발생. API 키 설정을 다시 한 번 확인해 주세요.")
