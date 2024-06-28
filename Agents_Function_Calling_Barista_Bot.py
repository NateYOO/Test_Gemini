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
COFFEE_BOT_PROMPT = COFFEE_BOT_PROMPT = """You are an order-taking system at a cafe in Korea. You must accurately understand customer orders and respond politely. You can only take orders for drinks on the menu and should politely guide customers if they request items not on the menu.

Ordering process:
1. Listen to and understand the customer's order.
2. Accurately capture and confirm the order details.
3. Check if there are any additional orders or modifications.
4. Confirm the entire order when it's complete.

Important notes:
- Always use a friendly and polite tone.
- Make sure you've understood the customer's request correctly.
- Refer to previous conversation content to maintain consistency in your responses.
- If a menu item is requested that's not available, recommend similar items.
- When confirming an order, accurately read back all items and options.

Menu:
Coffee Drinks:
- Americano (HOT/ICE)
- Cafe Latte (HOT/ICE)
- Vanilla Latte (HOT/ICE)
- Cappuccino (HOT)
- Caramel Macchiato (HOT/ICE)
- Espresso

Non-Coffee Drinks:
- Green Tea Latte (HOT/ICE)
- Hot Chocolate (HOT/ICE)
- Yuzu Tea (HOT/ICE)
- Chamomile Tea (HOT)
- Peppermint Tea (HOT)

Options:
- Milk options: Regular, Low-fat, Non-fat, Soy, Oat milk
- Syrup additions: Vanilla, Hazelnut, Caramel (500 won per pump)
- Extra shot (500 won per shot)
- Add whipped cream (500 won)

Sizes:
- Regular (R)
- Large (L) (500 won extra)

Operating hours: Daily from 7 AM to 10 PM

Prices:
- Espresso: 3,000 won
- All other drinks: Regular 4,500 won, Large 5,000 won
- Additional costs for options as noted above

Special notices:
- Today's recommended menu: Vanilla Latte
- Seasonal limited menu: Pistachio Latte (HOT/ICE)

When ordering, "hot" is considered HOT, "cold" or "iced" is considered ICE.
If a customer just says "(drink name) please", it's assumed to be HOT and Regular size.

Please take and process customer orders based on this information. When the order is complete, say "Enjoy your drink!"."""

# 주문 관리 함수들
def add_to_order(drink: str, modifiers: List[str] = []) -> None:
    st.session_state.current_order.append((drink, modifiers))

def get_order() -> List[Tuple[str, List[str]]]:
    return st.session_state.current_order

def clear_order() -> None:
    st.session_state.current_order = []

def confirm_order() -> None:
    st.session_state.order_confirmed = True

def place_order() -> int:
    st.session_state.placed_order = st.session_state.current_order.copy()
    clear_order()
    return 5  # 예상 대기 시간 (분)

# Gemini 모델 설정
model = genai.GenerativeModel('gemini-1.0-pro')

# 세션 상태 초기화
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'current_order' not in st.session_state:
    st.session_state.current_order = []
if 'order_confirmed' not in st.session_state:
    st.session_state.order_confirmed = False
if 'placed_order' not in st.session_state:
    st.session_state.placed_order = []
if 'convo' not in st.session_state:
    st.session_state.convo = model.start_chat(history=[
        {'role': 'user', 'parts': [COFFEE_BOT_PROMPT]},
        {'role': 'model', 'parts': ['네, 이해했습니다. 최선을 다해 주문을 받겠습니다!']}
    ])

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

    # 현재 주문 상태 추가
    current_order_status = f"현재 주문 상태: {st.session_state.current_order}"
    
    # 봇 응답
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        for response in st.session_state.convo.send_message(prompt + "\n" + current_order_status, stream=True):
            full_response += response.text
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})

# 현재 주문 상태 표시
st.sidebar.header("현재 주문")
if st.session_state.current_order:
    for idx, (drink, modifiers) in enumerate(st.session_state.current_order, 1):
        st.sidebar.write(f"{idx}. {drink}")
        if modifiers:
            st.sidebar.write(f"   - {', '.join(modifiers)}")
else:
    st.sidebar.write("아직 주문 내역이 없습니다.")

# 주문 확인 및 제출 버튼
if st.session_state.current_order and not st.session_state.order_confirmed:
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
        st.session_state.current_order = []
        st.session_state.order_confirmed = False
        st.session_state.placed_order = []
        st.experimental_rerun()
