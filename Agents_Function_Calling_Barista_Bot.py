import streamlit as st
import google.generativeai as genai
from typing import List, Tuple

# Streamlit 페이지 설정
st.set_page_config(page_title="Barista Bot", page_icon="☕")

# Gemini API 설정
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("GOOGLE_API_KEY not found in Streamlit secrets. Please set it up.")
    st.stop()
genai.configure(api_key=st.secrets["AIzaSyAbHQK9OtDTG5x5P1L_9YCnj7DwwoKf88w"])

# 상수 및 전역 변수
COFFEE_BOT_PROMPT = """You are a coffee order taking system...
# (여기에 전체 프롬프트 내용을 넣으세요)
"""

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
    {'role': 'model', 'parts': ['OK I understand. I will do my best!']}
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
st.title("☕ Barista Bot")
st.write("Welcome! I'm here to take your coffee order.")

# 채팅 메시지 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 사용자 입력
if prompt := st.chat_input("What would you like to order?"):
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
st.sidebar.header("Current Order")
if st.session_state.order:
    for idx, (drink, modifiers) in enumerate(st.session_state.order, 1):
        st.sidebar.write(f"{idx}. {drink}")
        if modifiers:
            st.sidebar.write(f"   - {', '.join(modifiers)}")
else:
    st.sidebar.write("No items in the order yet.")

# 주문 확인 및 제출 버튼
if st.session_state.order and not st.session_state.order_confirmed:
    if st.sidebar.button("Confirm Order"):
        confirm_order()
        st.sidebar.success("Order confirmed!")

if st.session_state.order_confirmed and not st.session_state.placed_order:
    if st.sidebar.button("Place Order"):
        wait_time = place_order()
        st.sidebar.success(f"Order placed! Estimated wait time: {wait_time} minutes")

# 주문 완료 후 메시지
if st.session_state.placed_order:
    st.sidebar.header("Order Placed")
    for idx, (drink, modifiers) in enumerate(st.session_state.placed_order, 1):
        st.sidebar.write(f"{idx}. {drink}")
        if modifiers:
            st.sidebar.write(f"   - {', '.join(modifiers)}")
    st.sidebar.write("Thank you for your order!")

# 새 주문 시작 버튼
if st.session_state.placed_order:
    if st.sidebar.button("Start New Order"):
        st.session_state.order = []
        st.session_state.order_confirmed = False
        st.session_state.placed_order = []
        st.experimental_rerun()
