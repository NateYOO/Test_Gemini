import streamlit as st
import google.generativeai as genai
from typing import List, Dict
from datetime import datetime
import json
import time
import logging
from google.api_core.exceptions import ResourceExhausted, GoogleAPIError

# Streamlit 페이지 설정
st.set_page_config(page_title="바리스타 봇", page_icon="☕", layout="wide")

# Gemini API 설정
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("GOOGLE_API_KEY가 Streamlit secrets에 없습니다. 설정해 주세요.")
    st.stop()
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Configure logging
logging.basicConfig(level=logging.INFO)

# 상수 및 전역 변수
COFFEE_BOT_PROMPT = """당신은 한국의 카페에서 주문을 받는 시스템입니다. 고객의 주문을 정확하게 이해하고 친절하게 응대해야 합니다. 메뉴에 있는 음료만 주문받을 수 있으며, 메뉴에 없는 요청에 대해서는 정중하게 안내해야 합니다.
 - 다양한 사이즈 요청을 이해하고 주문을 받습니다.
 - 사용자가 원하는 요청에 따라 금액을 정확히 계산하고 출력합니다.
 - 친절한게 응답합니다."""

MENU = {
    "커피 음료": {
        "아메리카노": {"price": 4500, "options": ["HOT", "ICE"]},
        "카페라떼": {"price": 5000, "options": ["HOT", "ICE"]},
        "바닐라라떼": {"price": 5500, "options": ["HOT", "ICE"]},
        "카푸치노": {"price": 5000, "options": ["HOT"]},
        "카라멜마키아또": {"price": 5500, "options": ["HOT", "ICE"]},
        "에스프레소": {"price": 3000, "options": ["HOT"]},
    },
    "논커피 음료": {
        "녹차라떼": {"price": 5500, "options": ["HOT", "ICE"]},
        "초콜릿": {"price": 5000, "options": ["HOT", "ICE"]},
        "유자차": {"price": 5000, "options": ["HOT", "ICE"]},
        "캐모마일티": {"price": 4500, "options": ["HOT"]},
        "페퍼민트티": {"price": 4500, "options": ["HOT"]},
    }
}

SIZES = {"Regular": 0, "Large": 500}
OPTIONS = {
    "샷 추가": 500,
    "휘핑크림 추가": 500,
    "바닐라 시럽": 500,
    "헤이즐넛 시럽": 500,
    "카라멜 시럽": 500
}

SIZE_KEYWORDS = {
    "Large": ["large", "큰", "크게", "사이즈업", "라지", "큰 거", "큰거", "큰 사이즈", "대형", "맥시멈"],
    "Regular": ["regular", "보통", "중간", "기본", "스탠다드", "작은", "작게", "small", "작은 거", "작은거", "작은 사이즈"]
}

# Retry decorator with exponential backoff
def retry(max_attempts=5, initial_wait=1, backoff_factor=2):
    def decorator(func):
        def wrapper(*args, **kwargs):
            wait_time = initial_wait
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except ResourceExhausted as e:
                    logging.warning(f"Resource exhausted. Retrying in {wait_time} seconds... (Attempt {attempt + 1}/{max_attempts})")
                    time.sleep(wait_time)
                    wait_time *= backoff_factor
                except GoogleAPIError as e:
                    logging.error(f"Google API error: {e}")
                    break
            raise ResourceExhausted("Exceeded maximum retry attempts")
        return wrapper
    return decorator

# 주문 및 사용자 관리 함수
def parse_order(message: str) -> Dict:
    message = message.lower()
    order = {}
    
    for category, items in MENU.items():
        for item, details in items.items():
            if item.lower() in message:
                order['drink'] = item
                break
        if 'drink' in order:
            break
    
    for size, keywords in SIZE_KEYWORDS.items():
        if any(keyword in message for keyword in keywords):
            order['size'] = size
            break
    
    options = [option for option in OPTIONS if option in message]
    if options:
        order['options'] = options
    
    return order

@retry(max_attempts=5, initial_wait=1, backoff_factor=2)
def get_bot_response(prompt):
    with st.spinner('봇 응답을 기다리는 중...'):
        try:
            response = st.session_state.convo.send_message(prompt)
            return response
        except Exception as e:
            logging.error(f"Error in get_bot_response: {e}")
            st.error("봇 응답 중 오류가 발생했습니다.")
            return None

# Main function or script entry point
def main():
    st.sidebar.title("바리스타 봇 메뉴")
    st.sidebar.write("이곳에서 다양한 옵션을 선택할 수 있습니다.")
    
    if 'convo' not in st.session_state:
        st.session_state.convo = genai.Conversation()

    user_input = st.text_input("메시지를 입력하세요:", key="user_input")
    
    if st.button("전송"):
        if user_input:
            order_details = parse_order(user_input)
            st.write("주문 상세:", order_details)
            
            full_response = get_bot_response(user_input)
            if full_response:
                st.write("봇 응답:", full_response)
        else:
            st.error("메시지를 입력해 주세요.")

if __name__ == "__main__":
    main()
