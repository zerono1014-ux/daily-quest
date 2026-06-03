# 파일명: app.py
# 실행 명령: pip install streamlit google-generativeai && streamlit run app.py

import streamlit as st
import google.generativeai as genai
import json
import datetime
import os
import re

# 1. 페이지 설정은 무조건 최상단에 딱 한 번만!
st.set_page_config(
    page_title="Daily Quest Master",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 2. 모바일 CSS 및 기본 UI 스타일 완벽 통합
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1.5rem !important;
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
# 💾 1. 기기 로컬 DB 영구 저장 시스템 (파일 동기화)
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

# 로컬 파일 데이터 로드 후 세션 바인딩
local_data = load_local_db()

# 세션 상태 뼈대 구축 및 자동 복구
if 'db' not in st.session_state:
    st.session_state.db = {
        "is_setup_complete": local_data.get("is_setup_complete", False),
        "page": local_data.get("page", "main_select"),
        "selected_mains": local_data.get("selected_mains", []),
        "selected_subs": local_data.get("selected_subs", []),
        "sub_levels": local_data.get("sub_levels", {}),
        "quest_cycles": local_data.get("quest_cycles", {}),
        "archive": local_data.get("archive", []), # 내 보관함 데이터
        "active_quests": local_data.get("active_quests", {}), # 현재 생성된 과제 저장
        "vocab_lock_time": local_data.get("vocab_lock_time", {}),
        "coding_test_active": local_data.get("coding_test_active", False),
        "coding_test_idx": local_data.get("coding_test_idx", 0),
        "coding_test_score": local_data.get("coding_test_score", 0)
    }

def sync_db():
    """세션 상태의 변화를 로컬 DB 파일에 즉시 동기화(Commit)"""
    save_local_db(st.session_state.db)
""", unsafe_allow_html=True)

# 🔑 Secrets 및 API 연동
secret_key = st.secrets.get("api_key", "")
with st.sidebar:
    st.header("🎯 Master 세팅")
    if secret_key:
        st.success("🔒 Cloud Secrets 연동 완료")
        api_key = secret_key
    else:
        api_key = st.text_input("Gemini API Key 입력", type="password")
    if api_key:
        genai.configure(api_key=api_key)

# 기본 데이터베이스
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
# 🧠 2. AI 프롬프트 파이프라인 및 정규식 추출기
# ==========================================
def get_ai_clean_json(prompt):
    if not api_key:
        st.error("API 키가 누락되었습니다. 설정을 확인하세요.")
        return None
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        # 정규식을 활용해 복잡한 텍스트 찌꺼기 속에서 순수 JSON 오브젝트만 정밀 추출 (PRD 5.2조 준수)
        json_match = re.search(r"\{.*\}", response.text.strip(), re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        return json.loads(response.text.strip())
    except Exception as e:
        st.error(f"AI 데이터 모델 빌드 에러: {e}")
        return None

# 카테고리별 프롬프트 제어 장치
def ai_agent_hub(sub, level, opt=""):
    main = SUB_TO_MAIN[sub]
    if main == "외국어":
        return get_ai_clean_json(f"영어 교육 전문가이자 공학 기술 영어 멘토입니다. 토익(TOEIC) 고득점 필수 어휘와 IT·전자공학 분야의 기술 전문 용어(Technical Terms)가 혼합된 '{level}' 수준의 필수 영단어 5개와 암기 검증용 4지선다형 미니 퀴즈 3문항을 생성하세요. 반환 양식 JSON: {{\"words\": [{{\'en\': \'단어\', \'kr\': \'뜻\', \'example\': \'예문\'}}], \"quizzes\": [{{\'question\': \'질문\', \'options\': [\'보기1\',\'2\',\'3\',\'4\'], \'answer\': \'정답텍스트\'}}]}}")
    elif main == "운동":
        return get_ai_clean_json(f"전문 스포츠 트레이너입니다. 종목:{sub}, 수준:{level}, 장소 및 방식:{opt}에 가장 적합한 당일 운동 루틴 미션을 상세히 짜주세요. 장소가 집인 경우 절대 기구 없이 맨몸운동으로만 구성해야 합니다. 반환 양식 JSON: {{\"title\": \"루틴명\", \"list\": [{{\'name\': \'운동명\', \'sets\': \'세트/횟수\', \'tip\': \'자세 팁\'}}], \"comment\": \"멘토 한마디\"}}")
    elif main == "독서" and opt == "지문":
        return get_ai_clean_json(f"문해력 교육 전문가입니다. {sub} 분야의 {level} 난이도에 해당하는 500자 내외의 전문 비문학 지문을 직접 집필하고, 문해력 독해 과제 1문항과 해설을 출제하세요. 반환 양식 JSON: {{\"title\": \"제목\", \"passage\": \"본문내용\", \"task\": \"문제\", \"solution\": \"정답 해설\"}}")
    elif main == "독서" and opt == "추천":
        return get_ai_clean_json(f"도서 전문 큐레이터입니다. {sub} 분야 {level} 수준에 맞는 필독서 1권을 엄선해 추천하세요. 반환 양식 JSON: {{\"title\": \"책제목\", \"author\": \"저자\", \"reason\": \"추천이유\", \"summary\": \"3줄 요약\", \"action\": \"실생활 적용 과제\"}}")
    elif main == "시사":
        return get_ai_clean_json(f"글로벌 경제 및 대형 테크 자산 수석 분석가입니다. '{sub}' 영역과 거시 경제 지표를 연계하여, 특히 인공지능(AI)과 반도체 섹터 동향, 미국 대형 테크주(Microsoft, Alphabet, Netflix) 시황 변동성, 그리고 이란-미국 갈등 같은 중동 지정학적 리스크가 유가 및 글로벌 공급망에 미치는 경제적 나비효과를 집중 분석한 VIP용 심층 리포트를 작성하세요. 반환 양식 JSON: {{\"headline\": \"헤드라인\", \"summary\": \"핵심 3줄 요약\", \"deep_dive\": \"심층 배경지식 및 공급망 나비효과 분석\", \"impact\": \"향후 자산 시장 파급 효과\"}}")
    elif main == "코딩" and opt == "테스트":
        return get_ai_clean_json(f"컴퓨터공학과 교수입니다. '{sub}' 언어 능력을 판정하기 위한 10문항의 객관식 시험지를 출제하세요. 반드시 앞부분 3문제는 가장 쉬운 문법 기초, 중간 4문제는 자료구조 논리 설계, 마지막 3문제는 예외 처리 및 에러 함정 중심의 최고 난이도로 출제해야 합니다. 반환 양식 JSON: {{\"questions\": [{{\'num\': 문항번호, \'difficulty\': \'하/중/상\', \'question\': \'문제 내용\', \'options\': [\'1\',\'2\',\'3\',\'4\'], \'answer\': \'정답텍스트\'}}]}}")
    elif main == "코딩" and opt == "미션":
        return get_ai_clean_json(f"프로그래밍 전공 시니어 멘토입니다. 만약 언어가 '파이썬'인 경우, 교재 <새내기 파이썬>의 핵심 진도 범위(리스트 구조 제어, 조건문 논리 설계 등)를 적극 반영하고, 최종적으로 나만의 '개인 주식 포트폴리오 관리 시스템'을 구현하는 데 직결되는 연계 퀘스트를 설계하세요. 전공자가 놓치기 쉬운 치명적인 에러와 함정 개념 설명을 포함해야 합니다. 난이도: {level}. 반환 양식 JSON: {{\"title\": \"미션명\", \"task\": \"과제 조건\", \"trap\": \"⚠️ 주의할 함정/에러 개념\", \"tip\": \"실무 전공자 팁\"}}")

# ==========================================
# ⚙️ 3. 설정 변경 즉시 반영(Invalidate) 정책 엔진
# ==========================================
def handle_setting_change(sub, new_val, setting_type):
    """주기, 수준 변경 등 설정이 바뀌는 즉시 기존 과제를 폭파하고 재생성 (PRD 2.3조)"""
    current_setting = st.session_state.db[setting_type].get(sub)
    if current_setting != new_val:
        st.session_state.db[setting_type][sub] = new_val
        if sub in st.session_state.db["active_quests"]:
            del st.session_state.db["active_quests"][sub] # 즉시 파기
        sync_db()
        st.rerun()

# ==========================================
# 🕹️ 4. 1단계 온보딩 및 라우터 제어 (로컬 DB 우선)
# ==========================================
if not st.session_state.db["is_setup_complete"]:
    page = st.session_state.db["page"]
    
    if page == "main_select":
        st.title("🎯 대분류 카테고리 선택")
        st.write("관심 분야를 선택하세요 (기기 보관)")
        
        selected = set(st.session_state.db["selected_mains"])
        cols = st.columns(5)
        for idx, (name, icon) in enumerate(MAIN_CATS.items()):
            with cols[idx]:
                if st.button(f"{icon}\n{name}", key=f"m_{name}", type="primary" if name in selected else "secondary"):
                    selected.remove(name) if name in selected else selected.add(name)
                    st.session_state.db["selected_mains"] = list(selected)
                    sync_db()
                    st.rerun()
        
        st.markdown("---")
        if st.button("다음 단계로 ➡️", use_container_width=True):
            if not selected: st.error("최소 1개 이상의 카테고리를 선택해야 합니다.")
            else:
                st.session_state.db["page"] = "sub_select"
                sync_db()
                st.rerun()

    elif page == "sub_select":
        st.title("🔍 세부 종목 및 수준 설정")
        selected_subs = set(st.session_state.db["selected_subs"])
        
        for main in st.session_state.db["selected_mains"]:
            st.subheader(f"{MAIN_CATS[main]} {main}")
            sub_dict = SUB_CATS[main]
            sub_cols = st.columns(3)
            for idx, (sub_name, icon) in enumerate(sub_dict.items()):
                with sub_cols[idx % 3]:
                    is_sel = sub_name in selected_subs
                    if st.button(f"{icon} {sub_name}", key=f"s_{sub_name}", type="primary" if is_sel else "secondary"):
                        selected_subs.remove(sub_name) if is_sel else selected_subs.add(sub_name)
                        st.session_state.db["selected_subs"] = list(selected_subs)
                        if sub_name not in st.session_state.db["sub_levels"]:
                            st.session_state.db["sub_levels"][sub_name] = "초급"
                        if sub_name not in st.session_state.db["quest_cycles"]:
                            st.session_state.db["quest_cycles"][sub_name] = 1
                        sync_db()
                        st.rerun()
        
        if len(selected_subs) >= 10:
            st.warning("🚨 [과부하 경고] 종목이 너무 많습니다! 페이스 조절을 권장합니다.")
            
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

# ==========================================
# 📲 5. 메인 대시보드 및 상세 콘텐츠 연동 영역
# ==========================================
else:
    # 상단 탭 구조 분화: 대시보드 홈 / 내 보관함 스크랩북
    menu_tab, archive_tab = st.tabs(["🔥 나의 퀘스트 대시보드", "📥 내 보관함 (스크랩북)"])
    
    with menu_tab:
        # 특정 종목 진입 여부 체크용 세션 변수
        if "current_sub_view" not in st.session_state:
            st.session_state.current_sub_view = None
            
        # [메인 홈: 아이콘 뷰 모드]
        if st.session_state.current_sub_view is None:
            st.title("🎯 Daily Quest Master")
            st.write("과제를 시작할 종목 아이콘을 클릭하세요.")
            
            # 아이콘 배치 그리드 구성
            subs = st.session_state.db["selected_subs"]
            if not subs:
                st.info("선택된 종목이 없습니다. 우측 재설정 기능을 이용해 종목을 추가하세요.")
            
            for sub in subs:
                main_cat = SUB_TO_MAIN[sub]
                icon = SUB_CATS[main_cat][sub]
                # 네이티브 스타일의 대시보드 아이콘 버튼 구현
                if st.button(f"{icon} {sub} ({main_cat})", key=f"dash_{sub}"):
                    st.session_state.current_sub_view = sub
                    st.rerun()
            
            st.markdown("---")
            if st.button("⚙️ 카테고리 전체 재설정", type="secondary"):
                st.session_state.db["is_setup_complete"] = False
                st.session_state.db["page"] = "main_select"
                sync_db()
                st.rerun()
                
        # [상세 페이지 모드: 특정 종목 내부 뷰]
        else:
            sub = st.session_state.current_sub_view
            main = SUB_TO_MAIN[sub]
            level = st.session_state.db["sub_levels"].get(sub, "초급")
            cycle = st.session_state.db["quest_cycles"].get(sub, 1)
            
            # 뒤로가기 버튼
            if st.button("⬅️ 대시보드 홈으로 가기", key="back_to_dash"):
                st.session_state.current_sub_view = None
                st.rerun()
                
            st.title(f"{SUB_CATS[main][sub]} {sub} 상세 과제실")
            
            # ⚙️ 실시간 세팅 제어 상자 연동 (즉시 반영 정책 준수)
            with st.expander("🛠️ 본 종목 개별 난이도/주기 설정 변경"):
                new_lvl = st.selectbox("난이도 수정", ["초급", "중급", "고급"], index=["초급", "중급", "고급"].index(level), key=f"mod_lvl_{sub}")
                handle_setting_change(sub, new_lvl, "sub_levels")
                
                new_cyc = st.slider("갱신 주기 수정 (일)", 1, 7, int(cycle), key=f"mod_cyc_{sub}")
                handle_setting_change(sub, new_cyc, "quest_cycles")
                
                if st.button("❌ 이 종목 대시보드에서 삭제하기", type="primary"):
                    st.session_state.db["selected_subs"].remove(sub)
                    if sub in st.session_state.db["active_quests"]: del st.session_state.db["active_quests"][sub]
                    st.session_state.current_sub_view = None
                    sync_db()
                    st.rerun()

            st.markdown("---")
            
            # 💡 [업데이트 - 콜드 스타트 예외 조항 처리]
            # active_quests에 데이터가 없으면 즉시 실시간 AI 호출을 트리거함
            if sub not in st.session_state.db["active_quests"]:
                with st.spinner(f"AI 멘토가 '{sub}' 맞춤형 고품격 과제를 빌드하는 중..."):
                    if main == "외국어":
                        st.session_state.db["active_quests"][sub] = ai_agent_hub(sub, level)
                    elif main == "운동":
                        st.session_state.db["active_quests"][sub] = ai_agent_hub(sub, level, opt="집 (맨몸)")
                    elif main == "독서":
                        st.session_state.db["active_quests"][sub] = {
                            "passage_data": ai_agent_hub(sub, level, opt="지문"),
                            "book_data": ai_agent_hub(sub, level, opt="추천")
                        }
                    elif main == "시사":
                        st.session_state.db["active_quests"][sub] = ai_agent_hub(sub, level)
                    elif main == "코딩":
                        st.session_state.db["active_quests"][sub] = {
                            "daily_mission": ai_agent_hub(sub, level, opt="미mission" if sub != "파이썬" else "미션")
                        }
                    sync_db()

            quest_data = st.session_state.db["active_quests"].get(sub)

            # ------------------------------------------------
            # 세부 종목별 UI 및 로직 핸들링 분기
            # ------------------------------------------------
            if main == "외국어" and quest_data:
                if sub == "영단어":
                    st.markdown("<div class='quest-card'><b>🌍 공학 기술 및 토익 필수 어휘집</b></div>", unsafe_allow_html=True)
                    content_str = ""
                    for w in quest_data.get('words', []):
                        st.markdown(f"**{w['en']}** : {w['kr']}\n\n*💡 예문:* {w['example']}")
                        content_str += f"■ {w['en']} : {w['kr']} (예문: {w['example']})\n"
                    
                    # 내 보관함 스크랩 연동
                    if st.button("🗂️ 본 단어장 앱 내 보관함에 스크랩 저장", key=f"scr_{sub}"):
                        st.session_state.db["archive"].append({"type": "영단어장", "date": str(datetime.date.today()), "content": content_str})
                        sync_db()
                        st.success("보관함 저장 완료!")

                    # 3시간 타임락 제어 로직
                    if sub not in st.session_state.db["vocab_lock_time"]:
                        st.session_state.db["vocab_lock_time"][sub] = str(datetime.datetime.now())
                        sync_db()
                    
                    start_time = datetime.datetime.fromisoformat(st.session_state.db["vocab_lock_time"][sub])
                    elapsed = (datetime.datetime.now() - start_time).total_seconds()
                    lock_duration = 10800 # 3시간
                    remains = lock_duration - elapsed
                    
                    st.write("---")
                    if remains > 0:
                        st.markdown(f"<div class='lock-card'>🔒 <b>암기 시간 보장 타임락 작동 중</b><br>단어 숙지를 위해 3시간 동안 검증 퀴즈가 잠깁니다.<br>⏳ 남은 시간: {int(remains//3600)}시간 {int((remains%3600)//60)}분</div>", unsafe_allow_html=True)
                        if st.button("🔓 [디버그용] 타임락 즉시 해제", key="bypass_lock"):
                            st.session_state.db["vocab_lock_time"][sub] = str(datetime.datetime.now() - datetime.timedelta(hours=4))
                            sync_db()
                            st.rerun()
                    else:
                        st.subheader("🌙 2단계: 암기 검증 미니 퀴즈")
                        for i, q in enumerate(quest_data.get('quizzes', [])):
                            st.radio(f"Q{i+1}. {q['question']}", q['options'], key=f"quiz_v_{i}")
                else:
                    # 리스닝 / 독해 일반 공통 UI
                    st.success("학습용 가이드 문서가 발급되었습니다.")
                    st.json(quest_data)

            elif main == "운동" and quest_data:
                st.subheader(f"💪 오늘의 추천 루틴: {quest_data.get('title')}")
                loc_opt = st.radio("장소 선택", ["집 (맨몸)", "헬스장 (기구)"], key="workout_loc_toggle", horizontal=True)
                
                # 장소 변경 시 즉시 AI 파기 및 재발급
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
                        with st.expander("💡 모범 답안 및 해설 보기"):
                            st.write(p_data.get("solution"))
                with t2:
                    b_data = quest_data.get("book_data")
                    if b_data:
                        st.success(f"『{b_data.get('title')}』 — 저자: {b_data.get('author')}")
                        st.write(f"**추천 사유:** {b_data.get('reason')}")
                        st.write(f"**핵심 3줄 요약:**\n{b_data.get('summary')}")
                        st.warning(f"🎯 실생활 액션 플랜 퀘스트: {b_data.get('action')}")

            elif main == "시사" and quest_data:
                # 아침 8시 타임 해제 락 검사 (KST 기준)
                kst_hour = (datetime.datetime.utcnow() + datetime.timedelta(hours=9)).hour
                if kst_hour < 8:
                    st.markdown("<div class='lock-card'>⏳ <b>오늘의 최고급 시사 리포트 발행 대기 중</b><br>매일 오전 8시 정각(KST)에 AI 심층 분석 브리핑이 자동 언락됩니다.</div>", unsafe_allow_html=True)
                    if st.button("🔓 [디버그용] 8시 락 우회 강제 오픈"):
                        kst_hour = 9 # 임의 해제
                
                if kst_hour >= 8:
                    st.header(quest_data.get("headline"))
                    st.success(f"**[VIP 핵심 3줄 요약]**\n{quest_data.get('summary')}")
                    st.markdown("### 🔍 Deep Dive (심층 배경 및 공급망 파급 효과)")
                    st.write(quest_data.get("deep_dive"))
                    st.markdown("### 🚀 Future Impact (향후 자산 시장 파급 효과)")
                    st.info(quest_data.get("impact"))
                    
                    rep_str = f"[{quest_data.get('headline')}]\n\n요약:\n{quest_data.get('summary')}\n\n본문:\n{quest_data.get('deep_dive')}\n\n영향:\n{quest_data.get('impact')}"
                    if st.button("🗂️ 본 리포트 앱 내 보관함에 스크랩 저장", key=f"scr_news_{sub}"):
                        st.session_state.db["archive"].append({"type": "시사리포트", "date": str(datetime.date.today()), "content": rep_str})
                        sync_db()
                        st.success("보관함 스크랩 완료!")

            elif main == "코딩":
                # 실력 진단 레벨 테스트 미이행 상태 처리
                if f"level_certified_{sub}" not in st.session_state.db:
                    st.markdown("<div class='lock-card'>📝 <b>역량 등급 산정을 위한 정밀 레벨 테스트 필요</b><br>합리적 맞춤 과제 배정을 위해 10문항 진단을 선행합니다. (하->중->상 순차 출제)</div>", unsafe_allow_html=True)
                    
                    if not st.session_state.db["coding_test_active"]:
                        if st.button("📝 레벨 테스트 문제지 출제받기", type="primary"):
                            with st.spinner("교수 아키텍트 에이전트가 시험지 마킹 중..."):
                                test_paper = ai_agent_hub(sub, "전체", opt="테스트")
                                if test_paper:
                                    st.session_state.test_questions = test_paper.get("questions", [])
                                    st.session_state.db["coding_test_active"] = True
                                    st.session_state.db["coding_test_idx"] = 0
                                    st.session_state.db["coding_test_score"] = 0
                                    sync_db()
                                    st.rerun()
                    else:
                        idx = st.session_state.db["coding_test_idx"]
                        questions = st.session_state.get("test_questions", [])
                        
                        if idx < len(questions):
                            q = questions[idx]
                            # 차등 배점 텍스트 안내 다듬기
                            st.markdown(f"### 문항 {idx+1}/10 ── 난이도: [{q.get('difficulty')}] (배점: {5 if q.get('difficulty')=='하' else 10 if q.get('difficulty')=='중' else 15}점)")
                            st.info(q.get("question"))
                            u_ans = st.radio("정답 선택", q.get("options"), key=f"test_ans_{idx}")
                            
                            if st.button("다음 문제 제출 ➡️"):
                                # 채점 스코어링 가중치 연산
                                if u_ans == q.get("answer"):
                                    weight = 5 if q.get('difficulty') == '하' else 10 if q.get('difficulty') == '중' else 15
                                    st.session_state.db["coding_test_score"] += weight
                                st.session_state.db["coding_test_idx"] += 1
                                sync_db()
                                st.rerun()
                        else:
                            # 10문항 종료 최종 정산 및 수준 확정 (PRD 커트라인 준수)
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
                                # 난이도가 바꼈으므로 기존 빈 퀘스트 파기
                                if sub in st.session_state.db["active_quests"]: del st.session_state.db["active_quests"][sub]
                                sync_db()
                                st.rerun()
                else:
                    # 등급 인증 완료 후 데일리 과제 UI
                    m_data = quest_data.get("daily_mission")
                    if m_data:
                        st.subheader(f"🎯 데일리 코딩 미션: {m_data.get('title')}")
                        st.code(m_data.get('task'), language=sub.lower())
                        st.error(f"{m_data.get('trap')}")
                        st.caption(f"💡 전공 시니어 팁: {m_data.get('tip')}")

    # ==========================================
    # 🗂️ 6. 신설: 앱 내 보관함 / 스크랩북 기능
    # ==========================================
    with archive_tab:
        st.title("🗂️ 나의 스크랩 북")
        st.write("앱 안에서 언제든 복습할 수 있는 소장용 보관함입니다.")
        
        archived_items = st.session_state.db.get("archive", [])
        if not archived_items:
            st.info("아직 스크랩한 콘텐츠가 없습니다. 과제실 내부에서 스크랩 버튼을 눌러보세요.")
        else:
            for i, item in enumerate(reversed(archived_items)):
                with st.expander(f"📌 [{item['type']}] 스크랩 일자: {item['date']}"):
                    st.text(item['content'])
                    if st.button("삭제", key=f"del_arch_{i}"):
                        st.session_state.db["archive"].remove(item)
                        sync_db()
                        st.rerun()
