import streamlit as st
import google.generativeai as genai
from typing import List, Tuple

# Streamlit 페이지 설정
st.set_page_config(page_title="바리스타 봇", page_icon="☕")

# Gemini API 설정
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("GOOGLE_API_KEY가 Streamlit secrets에 없습니다. 설정해 주세요.")
    st.stop()
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# 상수 및 전역 변수
COFFEE_BOT_PROMPT = """당신은 한국의 카페에서 주문을 받는 시스템입니다. 고객의 주문을 정확하게 이해하고 친절하게 응대해야 합니다. 메뉴에 있는 음료만 주문받을 수 있으며, 메뉴에 없는 요청에 대해서는 정중하게 안내해야 합니다. 

주문 과정:
1. 고객의 주문을 듣고 이해합니다.
2. add_to_order 함수를 사용하여 주문을 추가합니다.
3. 추가 주문이 있는지 확인합니다.
4. 주문이 완료되면 confirm_order 함수를 사용하여 주문을 확인합니다.
5. 주문 확인 후 place_order 함수를 사용하여 주문을 완료합니다.

주의사항:
- 항상 친절하고 공손한 말투를 사용하세요.
- 고객의 요청을 정확히 이해했는지 확인하세요.
- 메뉴에 없는 항목을 요청할 경우, 유사한 메뉴를 추천해 주세요.
- 주문 확인 시 모든 항목과 옵션을 정확히 읽어주세요.

메뉴:
커피 음료:
- 아메리카노 (HOT/ICE)
- 카페라떼 (HOT/ICE)
- 바닐라라떼 (HOT/ICE)
- 카푸치노 (HOT)
- 카라멜마키아또 (HOT/ICE)
- 에스프레소

논커피 음료:
- 녹차라떼 (HOT/ICE)
- 초콜릿 (HOT/ICE)
- 유자차 (HOT/ICE)
- 캐모마일티 (HOT)
- 페퍼민트티 (HOT)

옵션:
- 우유 선택: 일반, 저지방, 무지방, 두유, 오트밀크
- 시럽 추가: 바닐라, 헤이즐넛, 카라멜 (펌프 당 500원)
- 샷 추가 (샷 당 500원)
- 휘핑크림 추가 (500원)

크기:
- Regular (R)
- Large (L) (500원 추가)

영업 시간: 매일 오전 7시 ~ 오후 10시

가격: 
- 에스프레소: 3,000원
- 다른 모든 음료: Regular 4,500원, Large 5,000원
- 옵션 추가 비용은 위 옵션 설명 참조

특별 안내:
- 오늘의 추천 메뉴: 바닐라라떼
- 제철 한정 메뉴: 피스타치오 라떼 (HOT/ICE)

주문 시 "따뜻한"은 HOT, "차가운"은 ICE로 간주합니다.
"(음료 이름) 주세요"라고 하면 기본 옵션(HOT, Regular 사이즈)으로 주문됩니다.

이 정보를 바탕으로 고객의 주문을 받고 처리해 주세요. 주문이 완료되면 "맛있게 드세요!"라고 인사해 주세요."""

# 주문 관리 함수들
def add_to_order(drink: str, modifiers: List[str] = []) -> None:
    st.session_state.order.append((drink, modifiers))

def get_order() -> List[Tuple[str, List[str]]]:
    return st.session_state.order

def remove_item(n: int) -> str:
    return st.session_state.order.pop(int(n) - 1)[0]

def clear_order() -> None:
    st.session_state.order.clear()

def confirm_order() -> None:
    st.session_state.order_confirmed = True

def place_order() -> int:
    st.session_state.placed_order = st.session_state.order.copy()
    clear_order()
    return 5  # 예상 대기 시간 (분)

# Gemini 모델 설정
model = genai.GenerativeModel('gemini-1.0-pro')
convo = model.start_chat(history=[
    {'role': 'user', 'parts': [COFFEE_BOT_PROMPT]},
    {'role': 'model', 'parts': ['네, 이해했습니다. 최선을 다해 주문을 받겠습니다!']}
])

# 세션 상태 초기화
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'order' not in st.session_state:
    st.session_state.order = []
if 'order_confirmed' not in st.session_state:
    st.session_state.order_confirmed = False
if 'placed_order' not in st.session_state:
    st.session_state.placed_order = []

# 헤더
st.title("☕ 바리스타 봇")
st.write("안녕하세요! 주문을 받아드리겠습니다.")

# 채팅 메시지 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 사용자 입력
if prompt := st.chat_input("무엇을 주문하시겠습니까?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 봇 응답
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        for response in convo.send_message(prompt, stream=True):
            full_response += response.text
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})

# 현재 주문 상태 표시
st.sidebar.header("현재 주문")
if st.session_state.order:
    for idx, (drink, modifiers) in enumerate(st.session_state.order, 1):
        st.sidebar.write(f"{idx}. {drink}")
        if modifiers:
            st.sidebar.write(f"   - {', '.join(modifiers)}")
else:
    st.sidebar.write("아직 주문 내역이 없습니다.")

# 주문 확인 및 제출 버튼
if st.session_state.order and not st.session_state.order_confirmed:
    if st.sidebar.button("주문 확인"):
        confirm_order()
        st.sidebar.success("주문이 확인되었습니다!")

if st.session_state.order_confirmed and not st.session_state.placed_order:
    if st.sidebar.button("주문 제출"):
        wait_time = place_order()
        st.sidebar.success(f"주문이 완료되었습니다! 예상 대기 시간: {wait_time}분")

# 주문 완료 후 메시지
if st.session_state.placed_order:
    st.sidebar.header("주문 완료")
    for idx, (drink, modifiers) in enumerate(st.session_state.placed_order, 1):
        st.sidebar.write(f"{idx}. {drink}")
        if modifiers:
            st.sidebar.write(f"   - {', '.join(modifiers)}")
    st.sidebar.write("주문해 주셔서 감사합니다!")

# 새 주문 시작 버튼
if st.session_state.placed_order:
    if st.sidebar.button("새 주문 시작"):
        st.session_state.order = []
        st.session_state.order_confirmed = False
        st.session_state.placed_order = []
        st.experimental_rerun()
