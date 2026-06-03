import streamlit as st
import google.generativeai as genai
import json
import datetime
import os
import re

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

secret_key = st.secrets.get("api_key", "")
if secret_key:
    genai.configure(api_key=secret_key)
else:
    api_key = st.sidebar.text_input("Gemini API Key 입력", type="password")
    if api_key:
        genai.configure(api_key=api_key)

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
# 🧠 2. AI 프롬프트 파이프라인 (오타 맹점 제거 완치본)
# ==========================================
def get_ai_clean_json(prompt):
    if not secret_key:
        st.error("API 키가 누락되었습니다. 설정을 확인하세요.")
        return None
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # 마크다운 찌꺼기 완벽 제거
        text = re.sub(r"```json|```", "", text).strip()
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        return json.loads(text)
    except Exception as e:
        st.error(f"AI 데이터 파싱 오류 발생. 새로고침 후 다시 시도해 주세요: {e}")
        return None

def ai_agent_hub(sub, level, opt=""):
    main = SUB_TO_MAIN[sub]
    if main == "외국어":
        return get_ai_clean_json(f"영어 교육 전문가이자 공학 기술 영어 멘토입니다. 토익(TOEIC) 필수 어휘와 IT 분야 기술 전문 용어가 혼합된 '{level}' 수준의 필수 영단어 5개와 암기 검증용 퀴즈 3문항을 생성하세요. 반환 양식 JSON: {{\"words\": [{{\"en\": \"단어\", \"kr\": \"뜻\", \"example\": \"예문\"}}], \"quizzes\": [{{\"question\": \"질문\", \"options\": [\"보기1\",\"보기2\",\"보기3\",\"보기4\"], \"answer\": \"정답텍스트\"}}]}}")
    elif main == "운동":
        return get_ai_clean_json(f"전문 스포츠 트레이너입니다. 종목:{sub}, 수준:{level}, 장소:{opt}에 맞는 루틴 미션을 상세히 짜주세요. 반환 양식 JSON: {{\"title\": \"루틴명\", \"list\": [{{\"name\": \"운동명\", \"sets\": \"세트/횟수\", \"tip\": \"자세 팁\"}}], \"comment\": \"멘토 한마디\"}}")
    elif main == "독서" and opt == "지문":
        return get_ai_clean_json(f"문해력 교육 전문가입니다. {sub} 분야의 {level} 난이도 비문학 지문을 직접 집필하고 독해 과제 1문항을 출제하세요. 반환 양식 JSON: {{\"title\": \"제목\", \"passage\": \"본문내용\", \"task\": \"문제\", \"solution\": \"정답 해설\"}}")
    elif main == "독서" and opt == "추천":
        return get_ai_clean_json(f"도서 전문 큐레이터입니다. {sub} 분야 필독서 1권을 엄선해 추천하세요. 반환 양식 JSON: {{\"title\": \"책제목\", \"author\": \"저자\", \"reason\": \"추천이유\", \"summary\": \"3줄 요약\", \"action\": \"실생활 적용 과제\"}}")
    elif main == "시사":
        return get_ai_clean_json(f"글로벌 테크 자산 수석 분석가입니다. '{sub}' 영역과 거시 경제 지표를 연계하여, 특히 인공지능(AI)과 반도체 섹터 동향, 미국 대형 테크주 시황 변동성, 그리고 중동 지정학적 리스크가 공급망에 미치는 나비효과 VIP용 심층 리포트를 작성하세요. 반환 양식 JSON: {{\"headline\": \"헤드라인\", \"summary\": \"핵심 3줄 요약\", \"deep_dive\": \"심층 분석\", \"impact\": \"자산 시장 파급 효과\"}}")
    elif main == "코딩" and opt == "테스트":
        return get_ai_clean_json(f"컴퓨터공학과 교수입니다. 다른 설명은 배제하고 오직 순수 JSON 데이터만 반환하세요. '{sub}' 언어 능력을 판정하기 위한 10문항의 객관식 시험지를 출제하세요. 반드시 앞부분 3문제는 가장 쉬운 문법 기초, 중간 4문제는 자료구조 논리 설계, 마지막 3문제는 예외 처리 및 에러 함정 중심의 최고 난이도로 출제해야 합니다. 반환 양식 JSON: {{\"questions\": [{{\"num\": 1, \"difficulty\": \"하/중/상\", \"question\": \"문제 내용\", \"options\": [\"보기1\",\"보기2\",\"보기3\",\"보기4\"], \"answer\": \"정답텍스트\"}}]}}")
    elif main == "코딩" and opt == "미션":
        return get_ai_clean_json(f"프로그래밍 전공 시니어 멘토입니다. 만약 언어가 '파이썬'인 경우 교재 <새내기 파이썬>의 핵심 범위(리스트 구조, 조건문 설계)를 반영하고 '개인 주식 포트폴리오 관리 시스템' 구현에 직결되는 {level} 난이도 연계 퀘스트를 설계하세요. 반환 양식 JSON: {{\"title\": \"미션명\", \"task\": \"과제 조건 코딩 요구사항\", \"trap\": \"⚠️ 주의할 함정/에러 개념 설명\", \"tip\": \"실무 전공자 팁\"}}")

# ==========================================
# ⚙️ 3. 설정 변경 즉시 반영 정책
# ==========================================
def handle_setting_change(sub, new_val, setting_type):
    current_setting = st.session_state.db[setting_type].get(sub)
    if current_setting != new_val:
        st.session_state.db[setting_type][sub] = new_val
        if sub in st.session_state.db["active_quests"]:
            del st.session_state.db["active_quests"][sub]
        sync_db()
        st.rerun()

# ==========================================
# 🕹️ 4. 온보딩 버튼 토글 콜백
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

# ==========================================
# 📲 5. 메인 대시보드 및 상세 콘텐츠 연동 영역
# ==========================================
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
            
            # [기획 기능] 코딩 대분류용 10문항 정밀 레벨 테스트 레이어
            if main == "코딩" and f"level_certified_{sub}" not in st.session_state.db:
                st.markdown("<div class='lock-card'>📝 <b>역량 등급 산정을 위한 정밀 레벨 테스트 필요</b><br>합리적 맞춤 과제 배정을 위해 10문항 진단을 선행합니다. (하->중->상 순차 출제)</div>", unsafe_allow_html=True)
                
                if not st.session_state.db["coding_test_active"]:
                    if st.button("📝 레벨 테스트 문제지 출제받기", type="primary"):
                        with st.spinner("교수 아키텍트 에이전트가 시험지 마킹 중..."):
                            test_paper = ai_agent_hub(sub, "전체", opt="테스트")
                            if test_paper and "questions" in test_paper:
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
                # 정규 정밀 데일리 콘텐츠 파트
                if sub not in st.session_state.db["active_quests"]:
                    with st.spinner("AI 멘토가 오늘의 데일리 퀘스트를 생성하는 중..."):
                        if main == "외국어": st.session_state.db["active_quests"][sub] = ai_agent_hub(sub, level)
                        elif main == "운동": st.session_state.db["active_quests"][sub] = ai_agent_hub(sub, level, opt="집 (맨몸)")
                        elif main == "독서":
                            st.session_state.db["active_quests"][sub] = {
                                "passage_data": ai_agent_hub(sub, level, opt="지문"),
                                "book_data": ai_agent_hub(sub, level, opt="추천")
                            }
                        elif main == "시사": st.session_state.db["active_quests"][sub] = ai_agent_hub(sub, level)
                        elif main == "코딩": st.session_state.db["active_quests"][sub] = {"daily_mission": ai_agent_hub(sub, level, opt="미션")}
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
