import streamlit as st
import json
import datetime
import os

# ==========================================
# 🎨 페이지 설정 및 모바일 CSS
# ==========================================
st.set_page_config(
    page_title="Daily Quest Master",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 480px; 
    }
    .stButton>button { width: 100%; border-radius: 12px; font-weight: bold; height: 3.4rem; margin-bottom: 0.6rem; transition: all 0.2s ease;}
    .icon-box { background-color: #1e293b; color: white; padding: 20px; border-radius: 16px; text-align: center; font-size: 24px; font-weight: bold; cursor: pointer; margin-bottom: 15px; box-shadow: 0px 4px 10px rgba(0,0,0,0.1); }
    .quest-card { background-color: #f8f9fa; padding: 18px; border-radius: 14px; border-left: 6px solid #3b82f6; margin-bottom: 15px; color: #1e293b; }
    .lock-card { background-color: #fef3c7; padding: 18px; border-radius: 14px; border-left: 6px solid #d97706; margin-bottom: 15px; color: #92400e; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 💾 1. 기기 로컬 DB 영구 저장 시스템
# ==========================================
DB_FILE = "daily_quest_local_db.json"

def load_local_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_local_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

local_data = load_local_db()

if 'db' not in st.session_state:
    st.session_state.db = {
        "is_setup_complete": local_data.get("is_setup_complete", False),
        "page": local_data.get("page", "main_select"),
        "selected_mains": local_data.get("selected_mains", []),
        "selected_subs": local_data.get("selected_subs", []),
        "sub_levels": local_data.get("sub_levels", {}),
        "quest_cycles": local_data.get("quest_cycles", {}),
        "archive": local_data.get("archive", []), 
        "active_quests": local_data.get("active_quests", {}), 
        "vocab_lock_time": local_data.get("vocab_lock_time", {}),
        "coding_test_active": local_data.get("coding_test_active", False),
        "coding_test_idx": local_data.get("coding_test_idx", 0),
        "coding_test_score": local_data.get("coding_test_score", 0)
    }

def sync_db():
    save_local_db(st.session_state.db)

MAIN_CATS = {"외국어": "🌍", "운동": "🏋️‍♂️", "독서": "📚", "시사": "📰", "코딩": "💻"}
SUB_CATS = {
    "외국어": {"영단어": "📝", "리스닝": "🎧", "독해": "📖"},
    "운동": {"웨이트": "💪", "러닝": "🏃‍♂️", "스트레칭": "🧘"},
    "독서": {"인문": "🧠", "경제": "📈", "기술": "🤖"},
    "시사": {"정치": "⚖️", "경제": "💰", "기술트렌드": "🚀", "미국 정세": "🇺🇸", "중국 동향": "🇨🇳", "일본 마켓": "🇯🇵"},
    "코딩": {"파이썬": "🐍", "C": "🔵", "Java": "☕"}
}
SUB_TO_MAIN = {sub: main for main, subs in SUB_CATS.items() for sub in subs}

# ==========================================
# 📦 2. 고품격 고정형 마스터 더미 데이터셋 (초고속 0초 응답 서버)
# ==========================================
def get_dummy_data(sub, level, opt=""):
    main = SUB_TO_MAIN[sub]
    
    if main == "외국어":
        return {
            "words": [
                {"en": "Impedance", "kr": "임피던스 (교류 회로에서 전류의 흐름을 방해하는 저항 성분)", "example": "The input impedance of the operational amplifier is extremely high."},
                {"en": "Asymmetric", "kr": "비대칭의", "example": "Asymmetric cryptography utilizes a public key and a private key."},
                {"en": "Volatility", "kr": "변동성 (주가 등의 가격이 급격히 오르내리는 정도)", "example": "The tech sector experienced high volatility after the earnings announcement."},
                {"en": "Alleviate", "kr": "완화하다, 경감하다", "example": "New supply chain strategies were implemented to alleviate the bottleneck."},
                {"en": "Precedent", "kr": "선례, 전례", "example": "This direct regulatory action has no historical precedent in the tech market."}
            ],
            "quizzes": [
                {"question": "교류 회로에서 복소수 형태로 표현되는 전체 저항 성분을 뜻하는 단어는?", "options": ["Impedance", "Capacitance", "Inductance", "Admittance"], "answer": "Impedance"},
                {"question": "주식 마켓에서 가격이 급격하게 요동치는 성질을 뜻하는 단어는?", "options": ["Liquidity", "Volatility", "Sustainability", "Flexibility"], "answer": "Volatility"},
                {"question": "대칭의 반대말로, 양쪽의 형태나 성질이 서로 다른 것을 뜻하는 영단어는?", "options": ["Symmetric", "Asymmetric", "Geetric", "Parametric"], "answer": "Asymmetric"}
            ]
        }
    elif main == "운동":
        return {
            "title": "🔥 전공자 브레인 리프레시 루틴",
            "list": [
                {"name": "맨몸 스쿼트 (하체 펌핑)", "sets": "4세트 x 20회", "tip": "무릎이 발끝 앞으로 나가지 않게 엉덩이를 깊숙이 빼세요."},
                {"name": "정석 푸쉬업 (가슴/삼두)", "sets": "4세트 x 15회", "tip": "코어에 힘을 빡 주고 몸통이 일직선이 되도록 유지하세요."},
                {"name": "플랭크 (코어 강화)", "sets": "3세트 x 1분", "tip": "엉덩이가 하늘로 솟거나 아래로 처지지 않게 일자를 만드세요."}
            ],
            "comment": "하루 종일 모니터 보느라 굽은 어깨랑 척추, 지금 안 펴면 나중에 디스크 터집니다. 당장 실시!"
        }
    elif main == "독서":
        if opt == "지문":
            return {
                "title": "💡 인공지능 시대의 행렬 변환과 데이터 압축 이론",
                "passage": "현대 컴퓨터 비전과 대형 언어 모델(LLM)에서 수조 개의 데이터를 실시간으로 처리할 수 있는 비결은 선형대수학의 '행렬(Matrix)'에 있다. 고화질 이미지는 수백만 개의 픽셀 데이터를 가지고 있어 연산 장치에 극심한 과부하를 준다. 이때 데이터의 손실을 최소화하면서 차원을 축소하는 특이값 분해(SVD) 알고리즘을 사용하면, 거대한 행렬을 소수의 핵심 벡터 스페이스로 압축할 수 있다. 이는 행렬을 싫어하는 사람들에게는 그저 복잡한 수식에 불과해 보이지만, 실무 엔지니어들에게는 무거운 인공지능 모델을 다이어트 시켜 서비스 디바이스에 심을 수 있게 만드는 핵심 치트키와 같다.",
                "task": "본문에서 설명한 특이값 분해(SVD)의 엔지니어링적 핵심 목적은 무엇인가?",
                "solution": "정답: 고차원의 거대한 행렬 데이터를 손실을 최소화하면서 차원을 축소(압축)하여 연산 과부하를 막기 위함입니다."
            }
        else:
            return {
                "title": "새내기 파이썬 (프로그래밍 입문 필수 도서)",
                "author": "천인국",
                "reason": "파이썬의 가장 기초적인 리스트 자료구조와 조건문 논리를 완벽하게 마스터할 수 있는 전공 초년생들의 바이블입니다.",
                "summary": "1. 변수와 연산자의 기본 개념 체득\n2. if-else 조건문을 활용한 프로그램 제어 흐름 설계\n3. 리스트와 딕셔너리를 활용한 데이터 스토리지 핸들링 기초",
                "action": "교재에 나오는 리스트 제어문 코드를 직접 타이핑해 보고, 나만의 미니 데이터베이스 뼈대를 구축해 보세요."
            }
    elif main == "시사":
        return {
            "headline": "🚨 VIP 시사 리포트: 중동 리스크와 테크 자산 공급망 나비효과 분석",
            "summary": "1. 이란-미국 지정학적 갈등 고조로 인한 국제 유가 변동성 급증\n2. 글로벌 반도체 및 AI 하드웨어 서플라이 체인 병목 현상 우려\n3. 마이크로소프트, 알파벳, 넷플릭스 등 빅테크 주가의 금리 및 매크로 민감도 증대",
            "deep_dive": "최근 이란과 미국의 갈등 격화는 단순한 군사적 긴장감을 넘어 글로벌 반도체 장비 및 AI 데이터센터 공급망에 치명적인 나비효과를 유발하고 있습니다. 특히 에너지 가격 상승은 대규모 서버 인프라를 가동하는 Microsoft와 Alphabet(구글)의 데이터센터 운영 비용 압박으로 직결됩니다. 더불어 반도체 섹터의 핵심 후공정 패키징 라인이 밀집된 아시아-유럽 물류 항로가 차단될 조짐을 보이면서 공급 부족 우려가 심화되고 있습니다. 반면, 이러한 공급망 충격 속에서도 실적 가시성이 확보된 AI 핵심 기술 보유 대형 Tech 기업들로 자산 배분이 쏠리는 현상이 관측됩니다.",
            "impact": "에너지 가격 폭등이 장기화될 경우 테크 섹터 내에서도 옥석 가리기가 심화될 것이며, 단기적으로 AI 인프라 자본 지출(CapEx)의 효율성이 높은 기업 중심으로 포트폴리오를 재편하는 전략이 유효합니다."
        }
    elif main == "코딩" and opt == "테스트":
        return {
            "questions": [
                {"num": 1, "difficulty": "하", "question": "C언어에서 정수형 변수를 선언할 때 사용하는 키워드는 무엇인가요?", "options": ["int", "float", "char", "double"], "answer": "int"},
                {"num": 2, "difficulty": "하", "question": "파이썬에서 리스트의 맨 끝에 새로운 요소를 추가하는 함수(메서드)는?", "options": ["append()", "insert()", "extend()", "add()"], "answer": "append()"},
                {"num": 3, "difficulty": "하", "question": "C언어에서 문자열 출력 후 자동으로 줄바꿈을 하기 위해 사용하는 이스케이프 문자는?", "options": ["\\n", "\\t", "\\b", "\\r"], "answer": "\\n"},
                {"num": 4, "difficulty": "중", "question": "파이썬에서 'if a in [1, 2, 3]:' 구문의 논리적 의미는 무엇인가요?", "options": ["a가 리스트 내에 존재하는지 검사", "a를 리스트에 추가", "a와 리스트를 병합", "리스트를 비우기"], "answer": "a가 리스트 내에 존재하는지 검사"},
                {"num": 5, "difficulty": "중", "question": "C언어에서 배열명 자체가 의미하는 것은 무엇인가요?", "options": ["배열의 첫 번째 요소의 주소값", "배열의 전체 크기", "배열의 마지막 데이터", "배열의 차원 수"], "answer": "배열의 첫 번째 요소의 주소값"},
                {"num": 6, "difficulty": "중", "question": "배열의 인덱스 범위를 초과하여 메모리에 접근할 때 파이썬에서 발생하는 치명적인 에러 명칭은?", "options": ["IndexError", "ValueError", "TypeError", "KeyError"], "answer": "IndexError"},
                {"num": 7, "difficulty": "중", "question": "구조체(Structure)와 배열(Array)의 가장 결정적인 차이점은 무엇인가요?", "options": ["배열은 동일 타입만, 구조체는 서로 다른 타입의 데이터 수집 가능", "구조체는 함수 내부에서 선언 불가능", "배열이 메모리를 훨씬 더 많이 소모함", "차이점이 전혀 없음"], "answer": "배열은 동일 타입만, 구조체는 서로 다른 타입의 데이터 수집 가능"},
                {"num": 8, "difficulty": "상", "question": "C언어에서 포인터 변수 변환 시 포인터 크기(32비트/64비트 시스템 환경)는 각각 몇 바이트인가요?", "options": ["4바이트 / 8바이트", "2바이트 / 4바이트", "8바이트 / 16바이트", "1바이트 / 2바이트"], "answer": "4바이트 / 8바이트"},
                {"num": 9, "difficulty": "상", "question": "파이썬에서 deepcopy(깊은 복사)와 copy(얕은 복사)의 결정적인 차이는?", "options": ["깊은 복사는 복사본의 내부 가변 객체까지 완전히 독립된 새 주소로 생성함", "얕은 복사만 메모리를 사용함", "깊은 복사는 리스트에만 적용 가능함", "속도는 깊은 복사가 10배 더 빠름"], "answer": "깊은 복사는 복사본의 내부 가변 객체까지 완전히 독립된 새 주소로 생성함"},
                {"num": 10, "difficulty": "상", "question": "메모리 누수(Memory Leak)를 방지하기 위해 C언어에서 malloc() 선언 후 반드시 쌍으로 호출해야 하는 메모리 해제 함수는?", "options": ["free()", "delete()", "clear()", "release()"], "answer": "free()"}
            ]
        }
    elif main == "코딩" and opt == "미션":
        return {
            "title": "🐍 나만의 AI 기반 주식 포트폴리오 자산 관리 모듈 설계",
            "task": "파이썬 리스트 구조와 if-else 조건문 논리를 활용하여 포트폴리오 자산(Microsoft, Alphabet, Netflix 등)의 비중이 50%를 초과할 경우 시스템 경고(Warning) 팝업 신호를 송출하는 핵심 제어 로직 함수를 완성하십시오.",
            "trap": "⚠️ [치명적 함정] 리스트의 인덱스 검색 루프 구동 시, 데이터 배열 범위를 벗어나는 'IndexError' 함정과 문자열과 정수형 타입을 혼동하여 더하는 'TypeError' 연산 에러를 철저히 방지해야 합니다.",
            "tip": "교재 <새내기 파이썬>의 리스트 탐색 제어 파트를 참고하여 에러 예외처리를 견고하게 캡슐화하십시오."
        }

# ==========================================
# 🕹️ 3. 온보딩 버튼 토글 콜백 함수
# ==========================================
def toggle_main(name):
    selected = set(st.session_state.db["selected_mains"])
    if name in selected: selected.remove(name)
    else: selected.add(name)
    st.session_state.db["selected_mains"] = list(selected)
    valid_subs = [sub for sub in st.session_state.db["selected_subs"] if SUB_TO_MAIN.get(sub) in st.session_state.db["selected_mains"]]
    st.session_state.db["selected_subs"] = valid_subs
    sync_db()

def toggle_sub(sub_name):
    selected_subs = set(st.session_state.db["selected_subs"])
    if sub_name in selected_subs: selected_subs.remove(sub_name)
    else:
        selected_subs.add(sub_name)
        if sub_name not in st.session_state.db["sub_levels"]:
            st.session_state.db["sub_levels"][sub_name] = "초급" 
        if sub_name not in st.session_state.db["quest_cycles"]:
            st.session_state.db["quest_cycles"][sub_name] = 1
    st.session_state.db["selected_subs"] = list(selected_subs)
    sync_db()

# ==========================================
# 📱 4. 라우터 및 화면 렌더링 파트
# ==========================================
if not st.session_state.db["is_setup_complete"]:
    page = st.session_state.db["page"]
    if page == "main_select":
        st.title("🎯 대분류 카테고리 선택")
        st.write("관심 분야를 선택하세요.")
        cols = st.columns(5)
        for idx, (name, icon) in enumerate(MAIN_CATS.items()):
            with cols[idx]:
                st.button(f"{icon}\n{name}", key=f"m_{name}", type="primary" if name in st.session_state.db["selected_mains"] else "secondary", on_click=toggle_main, args=(name,))
        st.markdown("---")
        if st.button("다음 단계로 ➡️", use_container_width=True):
            if not st.session_state.db["selected_mains"]: st.error("최소 1개 이상의 카테고리를 선택해야 합니다.")
            else:
                st.session_state.db["page"] = "sub_select"
                sync_db()
                st.rerun()

    elif page == "sub_select":
        st.title("🔍 세부 종목 및 수준 설정")
        for main in st.session_state.db["selected_mains"]:
            st.subheader(f"{MAIN_CATS[main]} {main}")
            sub_dict = SUB_CATS[main]
            sub_cols = st.columns(3)
            for idx, (sub_name, icon) in enumerate(sub_dict.items()):
                with sub_cols[idx % 3]:
                    st.button(f"{icon} {sub_name}", key=f"s_{sub_name}", type="primary" if sub_name in st.session_state.db["selected_subs"] else "secondary", on_click=toggle_sub, args=(sub_name,))
        
        selected_subs = st.session_state.db["selected_subs"]
        if selected_subs:
            st.markdown("---")
            st.subheader("⏱️ 종목별 세부 난이도 및 주기 입력")
            for sub in selected_subs:
                c1, c2 = st.columns(2)
                with c1:
                    lvl = st.selectbox(f"'{sub}' 수준", ["초급", "중급", "고급"], index=["초급", "중급", "고급"].index(st.session_state.db["sub_levels"].get(sub, "초급")), key=f"on_lvl_{sub}")
                    st.session_state.db["sub_levels"][sub] = lvl
                with c2:
                    cyc = st.slider(f"'{sub}' 갱신 주기 (일)", 1, 7, int(st.session_state.db["quest_cycles"].get(sub, 1)), key=f"on_cyc_{sub}")
                    st.session_state.db["quest_cycles"][sub] = cyc
            sync_db()

        st.markdown("---")
        cc1, cc2 = st.columns(2)
        with cc1:
            if st.button("⬅️ 뒤로 가기"):
                st.session_state.db["page"] = "main_select"
                sync_db()
                st.rerun()
        with cc2:
            if st.button("✅ 앱 세팅 완료"):
                if not selected_subs: st.error("최소 1개 이상의 세부 종목을 선택하세요.")
                else:
                    st.session_state.db["is_setup_complete"] = True
                    sync_db()
                    st.rerun()

# 메인 대시보드 홈
else:
    menu_tab, archive_tab = st.tabs(["🔥 나의 퀘스트 대시보드", "📥 내 보관함 (스크랩북)"])
    
    with menu_tab:
        if "current_sub_view" not in st.session_state: st.session_state.current_sub_view = None
            
        if st.session_state.current_sub_view is None:
            st.title("🎯 Daily Quest Master")
            st.write("과제를 시작할 종목 아이콘을 클릭하세요.")
            subs = st.session_state.db["selected_subs"]
            for sub in subs:
                main_cat = SUB_TO_MAIN[sub]
                icon = SUB_CATS[main_cat][sub]
                if st.button(f"{icon} {sub} ({main_cat})", key=f"dash_{sub}"):
                    st.session_state.current_sub_view = sub
                    st.rerun()
            st.markdown("---")
            if st.button("⚙️ 카테고리 전체 재설정", type="secondary"):
                st.session_state.db["is_setup_complete"] = False
                st.session_state.db["page"] = "main_select"
                st.session_state.db["selected_mains"] = []
                st.session_state.db["selected_subs"] = []
                st.session_state.db["active_quests"] = {}
                sync_db()
                st.rerun()
                
        else:
            sub = st.session_state.current_sub_view
            main = SUB_TO_MAIN[sub]
            level = st.session_state.db["sub_levels"].get(sub, "초급")
            cycle = st.session_state.db["quest_cycles"].get(sub, 1)
            
            if st.button("⬅️ 대시보드 홈으로 가기", key="back_to_dash"):
                st.session_state.current_sub_view = None
                st.rerun()
                
            st.title(f"{SUB_CATS[main][sub]} {sub} 상세 과제실")
            st.markdown("---")
            
            # 🚨 [기획 완벽 유지] 코딩 대분류 전용 10문항 정밀 레벨 테스트 레이어
            if main == "코딩" and f"level_certified_{sub}" not in st.session_state.db:
                st.markdown("<div class='lock-card'>📝 <b>역량 등급 산정을 위한 정밀 레벨 테스트 필요</b><br>합리적 맞춤 과제 배정을 위해 10문항 진단을 선행합니다. (하->중->상 순차 출제)</div>", unsafe_allow_html=True)
                
                if not st.session_state.db["coding_test_active"]:
                    if st.button("📝 레벨 테스트 문제지 출제받기", type="primary"):
                        test_paper = get_dummy_data(sub, "전체", opt="테스트")
                        st.session_state.test_questions = test_paper.get("questions", [])
                        st.session_state.db["coding_test_active"] = True
                        st.session_state.db["coding_test_idx"] = 0
                        st.session_state.db["coding_test_score"] = 0
                        sync_db()
                        st.rerun()
                else:
                    idx = st.session_state.db["coding_test_idx"]
                    questions = st.session_state.get("test_questions", [])
                    
                    if questions and idx < len(questions):
                        q = questions[idx]
                        weight = 5 if q.get('difficulty')=='하' else 10 if q.get('difficulty')=='중' else 15
                        st.markdown(f"### 문항 {idx+1}/10 ── 난이도: [{q.get('difficulty')}] (배점: {weight}점)")
                        st.info(q.get("question"))
                        
                        options = q.get("options", ["1", "2", "3", "4"])
                        u_ans = st.radio("정답 선택", options, key=f"test_ans_{idx}")
                        
                        if st.button("다음 문제 제출 ➡️", key=f"btn_next_{idx}"):
                            if u_ans == q.get("answer"):
                                st.session_state.db["coding_test_score"] += weight
                            st.session_state.db["coding_test_idx"] += 1
                            sync_db()
                            st.rerun()
                    else:
                        final_score = st.session_state.db["coding_test_score"]
                        if final_score >= 81: certified_level = "고급"
                        elif final_score >= 46: certified_level = "중급"
                        else: certified_level = "초급"
                        
                        st.success(f"🎉 테스트 완주 성료! 최종 획득 점수: {final_score}점")
                        st.markdown(f"AI 등급 판정 결과: 사용자의 현재 역량은 **[{certified_level}]** 자입니다.")
                        
                        if st.button("본 등급 확정 및 과제실 입장"):
                            st.session_state.db[f"level_certified_{sub}"] = certified_level
                            st.session_state.db["sub_levels"][sub] = certified_level
                            st.session_state.db["coding_test_active"] = False
                            if sub in st.session_state.db["active_quests"]: del st.session_state.db["active_quests"][sub]
                            sync_db()
                            st.rerun()
            
            else:
                # 0초 만에 데이터를 가져오는 마스터 동기화 로직
                if sub not in st.session_state.db["active_quests"]:
                    if main == "외국어": st.session_state.db["active_quests"][sub] = get_dummy_data(sub, level)
                    elif main == "운동": st.session_state.db["active_quests"][sub] = get_dummy_data(sub, level, opt="집 (맨몸)")
                    elif main == "독서":
                        st.session_state.db["active_quests"][sub] = {
                            "passage_data": get_dummy_data(sub, level, opt="지문"),
                            "book_data": get_dummy_data(sub, level, opt="추천")
                        }
                    elif main == "시사": st.session_state.db["active_quests"][sub] = get_dummy_data(sub, level)
                    elif main == "coding": pass
                    elif main == "코딩": st.session_state.db["active_quests"][sub] = {"daily_mission": get_dummy_data(sub, level, opt="미션")}
                    sync_db()

                quest_data = st.session_state.db["active_quests"].get(sub)

                if main == "외국어" and quest_data:
                    if sub == "영단어":
                        st.markdown("<div class='quest-card'><b>🌍 공학 기술 및 토익 필수 어휘집</b></div>", unsafe_allow_html=True)
                        content_str = ""
                        for w in quest_data.get('words', []):
                            st.markdown(f"**{w['en']}** : {w['kr']}\n\n*💡 예문:* {w['example']}")
                            content_str += f"■ {w['en']} : {w['kr']} (예문: {w['example']})\n"
                        if st.button("🗂️ 본 단어장 앱 내 보관함에 스크랩 저장", key=f"scr_{sub}"):
                            st.session_state.db["archive"].append({"type": "영단어장", "date": str(datetime.date.today()), "content": content_str})
                            sync_db()
                            st.success("보관함 저장 완료!")

                        if sub not in st.session_state.db["vocab_lock_time"]:
                            st.session_state.db["vocab_lock_time"][sub] = str(datetime.datetime.now())
                            sync_db()
                        start_time = datetime.datetime.fromisoformat(st.session_state.db["vocab_lock_time"][sub])
                        elapsed = (datetime.datetime.now() - start_time).total_seconds()
                        remains = 10800 - elapsed
                        st.write("---")
                        if remains > 0:
                            st.markdown(f"<div class='lock-card'>🔒 <b>암기 시간 보장 타임락 작동 중</b><br>⏳ 남은 시간: {int(remains//3600)}시간 {int((remains%3600)//60)}분</div>", unsafe_allow_html=True)
                            if st.button("🔓 [디버그용] 타임락 즉시 해제", key="bypass_lock"):
                                st.session_state.db["vocab_lock_time"][sub] = str(datetime.datetime.now() - datetime.timedelta(hours=4))
                                sync_db()
                                st.rerun()
                        else:
                            st.subheader("🌙 2단계: 암기 검증 미니 퀴즈")
                            for i, q in enumerate(quest_data.get('quizzes', [])): st.radio(f"Q{i+1}. {q['question']}", q['options'], key=f"quiz_v_{i}")
                else:
                    st.success("학습용 가이드 문서가 발급되었습니다.")
                    st.json(quest_data)

                elif main == "운동" and quest_data:
                    st.subheader(f"💪 오늘의 추천 루틴: {quest_data.get('title')}")
                    loc_opt = st.radio("장소 선택", ["집 (맨몸)", "헬스장 (기구)"], key="workout_loc_toggle", horizontal=True)
                    if "last_loc" not in st.session_state: st.session_state.last_loc = "집 (맨몸)"
                    if st.session_state.last_loc != loc_opt:
                        st.session_state.last_loc = loc_opt
                        del st.session_state.db["active_quests"][sub]
                        sync_db()
                        st.rerun()
                    for i, ex in enumerate(quest_data.get('list', [])):
                        st.markdown(f"**{i+1}. {ex['name']}** — `{ex['sets']}`")
                        st.caption(f"💡 팁: {ex['tip']}")
                    st.info(f"🗣️ 코치 격려: {quest_data.get('comment')}")

                elif main == "독서" and quest_data:
                    t1, t2 = st.tabs(["📱 지문 읽기 및 과제", "📚 오늘의 도서 큐레이션"])
                    with t1:
                        p_data = quest_data.get("passage_data")
                        if p_data:
                            st.subheader(p_data.get("title"))
                            st.info(p_data.get("passage"))
                            st.markdown(f"**📝 문해력 과제:** {p_data.get('task')}")
                            st.text_area("내 답안 작성칸", key=f"read_ans_{sub}")
                    with t2:
                        b_data = quest_data.get("book_data")
                        if b_data:
                            st.success(f"『{b_data.get('title')}』 — 저자: {b_data.get('author')}")
                            st.write(f"**핵심 3줄 요약:**\n{b_data.get('summary')}")

                elif main == "시사" and quest_data:
                    kst_hour = (datetime.datetime.utcnow() + datetime.timedelta(hours=9)).hour
                    if kst_hour < 8:
                        st.markdown("<div class='lock-card'>⏳ <b>오전 8시 정각(KST) 분석 브리핑 자동 오픈 대기 중</b></div>", unsafe_allow_html=True)
                        if st.button("🔓 [디버그용] 8시 락 우회 강제 오픈"): kst_hour = 9 
                    if kst_hour >= 8:
                        st.header(quest_data.get("headline"))
                        st.success(f"**[VIP 핵심 3줄 요약]**\n{quest_data.get('summary')}")
                        st.markdown("### 🔍 Deep Dive (심층 배경 및 공급망 파급 효과)")
                        st.write(quest_data.get("deep_dive"))
                        st.markdown("### 🚀 Future Impact")
                        st.info(quest_data.get("impact"))

                elif main == "코딩" and quest_data:
                    m_data = quest_data.get("daily_mission")
                    if m_data:
                        st.subheader(f"🎯 데일리 코딩 미션: {m_data.get('title')}")
                        st.code(m_data.get('task'), language=sub.lower())
                        st.error(f"{m_data.get('trap')}")
                        st.caption(f"💡 전공 시니어 팁: {m_data.get('tip')}")

    with archive_tab:
        st.title("🗂️ 나의 스크랩 북")
        archived_items = st.session_state.db.get("archive", [])
        if not archived_items: st.info("아직 스크랩한 콘텐츠가 없습니다.")
        else:
            for i, item in enumerate(reversed(archived_items)):
                with st.expander(f"📌 [{item['type']}] 스크랩 일자: {item['date']}"):
                    st.text(item['content'])
                    if st.button("삭제", key=f"del_arch_{i}"):
                        st.session_state.db["archive"].remove(item)
                        sync_db()
                        st.rerun()
