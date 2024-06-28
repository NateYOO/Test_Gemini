import streamlit as st
import google.generativeai as genai
from datetime import datetime
import json
from utils import parse_order, get_missing_order_info, process_order, get_user_orders, calculate_daily_sales, mark_order_as_paid, cancel_order, change_order_size, display_menu, load_order_history, save_order_history, add_to_order_history, update_order_history, remove_from_order_history, get_user_order_history, get_bot_response

# Streamlit 페이지 설정
st.set_page_config(page_title="바리스타 봇", page_icon="☕", layout="wide")

# Gemini API 설정
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("GOOGLE_API_KEY가 Streamlit secrets에 없습니다. 설정해 주세요.")
    st.stop()
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# 주문 상태 초기화 함수
def initialize_order_state():
    if 'order_state' not in st.session_state:
        st.session_state.order_state = {
            'drink': None, 'size': None, 'temp': None,
            'options': [], 'confirmed': False, 'payment_method': None
        }

# 세션 상태 초기화
def initialize_session_state():
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'orders' not in st.session_state:
        st.session_state.orders = {}
    if 'current_user' not in st.session_state:
        st.session_state.current_user = "user1"
    if 'convo' not in st.session_state:
        model = genai.GenerativeModel('gemini-1.5-pro')
        st.session_state.convo = model.start_chat(history=[
            {'role': 'user', 'parts': [COFFEE_BOT_PROMPT]},
            {'role': 'model', 'parts': ["네, 이해했습니다. 주문을 받을 준비가 되었습니다!"]}
        ])
    initialize_order_state()

# 메인 애플리케이션
def main():
    st.title("☕ 바리스타 봇")

    # 메뉴 표시 토글
    if st.checkbox("메뉴 보기"):
        display_menu()

    st.write("안녕하세요! 주문하시겠습니까?")

    # 채팅 인터페이스
    chat_container = st.container()

    # 사용자 입력
    prompt = st.chat_input("주문을 입력해주세요.")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
            
            # 봇 응답
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = get_bot_response(prompt)
                message_placeholder.markdown(full_response)
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})

    # 결제 방법 선택
    if st.session_state.orders.get(st.session_state.current_user):
        latest_order = st.session_state.orders[st.session_state.current_user][-1]
        if not latest_order.get('payment_method'):
            payment_method = st.radio("결제 방법 선택:", ["현금", "카드", "모바일 결제"])
            if st.button("결제 확인"):
                latest_order['payment_method'] = payment_method
                st.success(f"결제 방법이 {payment_method}로 설정되었습니다.")
                st.experimental_rerun()

    # 사이드바 (주문 관리)
    with st.sidebar:
        st.title("주문 관리")
        
        st.selectbox("사용자 선택", ["user1", "user2", "user3"], key="current_user")

        st.header(f"{st.session_state.current_user}의 현재 주문")
        user_orders = get_user_orders(st.session_state.current_user)
        for idx, order in enumerate(user_orders):
            st.write(f"{idx + 1}. {order['drink']} ({order['size']}, {order['temp']})")
            st.write(f"   옵션: {', '.join(order['options'])}")
            st.write(f"   가격: {order['price']}원")
            st.write(f"   결제: {'완료' if order['paid'] else '미완료'}")
            st.write(f"   결제 방법: {order.get('payment_method', '미선택')}")
            
            col1, col2 = st.columns(2)
            with col1:
                if not order['paid']:
                    if st.button(f"결제 완료 (주문 {idx + 1})"):
                        mark_order_as_paid(st.session_state.current_user, idx)
                        st.experimental_rerun()
            with col2:
                if st.button(f"주문 취소 (주문 {idx + 1})"):
                    cancel_order(st.session_state.current_user, idx)
                    st.success(f"주문 {idx + 1}이 취소되었습니다.")
                    st.experimental_rerun()

        st.header("일일 매출")
        st.write(f"총액: {calculate_daily_sales()}원")

        if st.button("새 주문 시작"):
            st.session_state.messages = []
            initialize_order_state()
            st.experimental_rerun()

        # 주문 히스토리 표시
        st.header("주문 히스토리")
        user_history = get_user_order_history(st.session_state.current_user)
        for idx, order in enumerate(user_history, 1):
            st.write(f"{idx}. {order['drink']} ({order['size']}, {order['temp']})")
            st.write(f"   옵션: {', '.join(order['options'])}")
            st.write(f"   가격: {order['price']}원")
            st.write(f"   결제: {'완료' if order['paid'] else '미완료'}")
            st.write(f"   결제 방법: {order.get('payment_method', '미선택')}")
            st.write(f"   주문 시간: {order['timestamp']}")
            st.write("---")

        if st.button("주문 히스토리 초기화"):
            save_order_history({st.session_state.current_user: []})
            st.success("주문 히스토리가 초기화되었습니다.")
            st.experimental_rerun()

    # 메인 애플리케이션 끝
    st.write("바리스타 봇이 실행 중입니다. 주문을 입력해주세요.")

if __name__ == "__main__":
    initialize_session_state()
    main()
