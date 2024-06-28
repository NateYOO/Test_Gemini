import streamlit as st
import google.generativeai as genai
from datetime import datetime
import json

# Streamlit 페이지 설정
st.set_page_config(page_title="바리스타 봇", page_icon="☕", layout="wide")

# Gemini API 설정
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("GOOGLE_API_KEY가 Streamlit secrets에 없습니다. 설정해 주세요.")
    st.stop()
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# 상수 및 전역 변수
MENU = {
    "아메리카노": {"price": 4500, "options": ["HOT", "ICE"]},
    "카페라떼": {"price": 5000, "options": ["HOT", "ICE"]},
    "바닐라라떼": {"price": 5500, "options": ["HOT", "ICE"]},
    "카푸치노": {"price": 5000, "options": ["HOT"]},
    "카라멜마키아또": {"price": 5500, "options": ["HOT", "ICE"]},
    "에스프레소": {"price": 3000, "options": ["HOT"]},
}

SIZES = {"Regular": 0, "Large": 500}
OPTIONS = {
    "샷 추가": 500,
    "휘핑크림 추가": 500,
    "바닐라 시럽": 500,
    "헤이즐넛 시럽": 500,
    "카라멜 시럽": 500
}

COFFEE_BOT_PROMPT = """당신은 한국의 카페에서 주문을 받는 시스템입니다. 고객의 주문을 정확하게 이해하고 친절하게 응대해야 합니다. 메뉴에 있는 음료만 주문받을 수 있으며, 메뉴에 없는 요청에 대해서는 정중하게 안내해야 합니다.
 - 다양한 사이즈 요청을 이해하고 주문을 받습니다.
 - 사용자가 원하는 요청에 따라 금액을 정확히 계산하고 출력합니다.
 - 친절하게 응답합니다.
 - 주문 과정은 다음과 같습니다: 1. 음료 선택, 2. 온도 선택, 3. 사이즈 선택, 4. 옵션 선택, 5. 주문 확인, 6. 결제 방법 선택
 - 각 단계에서 사용자의 입력을 확인하고, 다음 단계로 안내합니다.
 - 주문이 완료되면 주문 내역과 총 금액을 알려줍니다.

현재 메뉴:
{menu}

사이즈:
{sizes}

추가 옵션:
{options}

현재 주문 상태:
{order_state}
"""

# 세션 상태 초기화
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'orders' not in st.session_state:
    st.session_state.orders = {}
if 'current_user' not in st.session_state:
    st.session_state.current_user = "user1"
if 'order_state' not in st.session_state:
    st.session_state.order_state = {
        'drink': None, 'size': None, 'temp': None,
        'options': [], 'confirmed': False, 'payment_method': None
    }
if 'convo' not in st.session_state:
    model = genai.GenerativeModel('gemini-1.5-pro')
    st.session_state.convo = model.start_chat(history=[])

# 주문 처리 함수
def process_order(user_id, order):
    drink = order['drink']
    size = order['size']
    temp = order['temp']
    options = order['options']
    
    base_price = MENU[drink]["price"]
    size_price = SIZES[size]
    options_price = sum(OPTIONS[option] for option in options)
    total_price = base_price + size_price + options_price

    new_order = {
        "drink": drink,
        "size": size,
        "temp": temp,
        "options": options,
        "price": total_price,
        "paid": False,
        "payment_method": None,
        "timestamp": datetime.now().isoformat()
    }
    
    if user_id not in st.session_state.orders:
        st.session_state.orders[user_id] = []
    st.session_state.orders[user_id].append(new_order)
    
    return f"{drink} ({size}, {temp}) 주문이 완료되었습니다. 가격: {total_price}원"

# Gemini API를 사용한 응답 생성 함수
def get_bot_response(user_input):
    prompt = COFFEE_BOT_PROMPT.format(
        menu=json.dumps(MENU, ensure_ascii=False, indent=2),
        sizes=json.dumps(SIZES, ensure_ascii=False, indent=2),
        options=json.dumps(OPTIONS, ensure_ascii=False, indent=2),
        order_state=json.dumps(st.session_state.order_state, ensure_ascii=False, indent=2)
    )
    
    st.session_state.convo.send_message(prompt)
    response = st.session_state.convo.send_message(user_input)
    
    return response.text

# 주문 상태 업데이트 함수
def update_order_state(response):
    state = st.session_state.order_state
    
    if "음료가 선택되었습니다" in response:
        state['drink'] = next((drink for drink in MENU if drink in response), None)
    elif "온도가 선택되었습니다" in response:
        state['temp'] = "HOT" if "HOT" in response else "ICE"
    elif "사이즈가 선택되었습니다" in response:
        state['size'] = "Large" if "Large" in response else "Regular"
    elif "옵션이 선택되었습니다" in response:
        state['options'] = [option for option in OPTIONS if option in response]
    elif "주문이 확인되었습니다" in response:
        state['confirmed'] = True
    elif "결제 방법이 선택되었습니다" in response:
        state['payment_method'] = next((method for method in ["현금", "카드", "모바일"] if method in response), None)
        if state['payment_method']:
            process_order(st.session_state.current_user, state)
            st.session_state.order_state = {
                'drink': None, 'size': None, 'temp': None,
                'options': [], 'confirmed': False, 'payment_method': None
            }

# 메인 애플리케이션
st.title("☕ 바리스타 봇")

# 메뉴 표시
if st.checkbox("메뉴 보기"):
    st.subheader("메뉴")
    for item, details in MENU.items():
        st.write(f"- {item}: {details['price']}원 ({'/'.join(details['options'])})")
    
    st.subheader("사이즈")
    for size, price in SIZES.items():
        st.write(f"- {size}: +{price}원")
    
    st.subheader("추가 옵션")
    for option, price in OPTIONS.items():
        st.write(f"- {option}: +{price}원")

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
            update_order_state(full_response)
        
        st.session_state.messages.append({"role": "assistant", "content": full_response})

# 사이드바 (주문 관리)
with st.sidebar:
    st.title("주문 관리")
    
    st.selectbox("사용자 선택", ["user1", "user2", "user3"], key="current_user")

    st.header(f"{st.session_state.current_user}의 현재 주문")
    user_orders = st.session_state.orders.get(st.session_state.current_user, [])
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
                    order['paid'] = True
                    st.success(f"주문 {idx + 1} 결제가 완료되었습니다.")
        with col2:
            if st.button(f"주문 취소 (주문 {idx + 1})"):
                st.session_state.orders[st.session_state.current_user].pop(idx)
                st.success(f"주문 {idx + 1}이 취소되었습니다.")

    st.header("일일 매출")
    total_sales = sum(order['price'] for orders in st.session_state.orders.values() for order in orders if order['paid'])
    st.write(f"총액: {total_sales}원")

    if st.button("새 주문 시작"):
        st.session_state.order_state = {
            'drink': None, 'size': None, 'temp': None,
            'options': [], 'confirmed': False, 'payment_method': None
        }
        st.session_state.messages = []
        st.session_state.convo = genai.GenerativeModel('gemini-1.5-pro').start_chat(history=[])
        st.success("새 주문을 시작합니다.")

if __name__ == "__main__":
    st.write("바리스타 봇이 실행 중입니다. 주문을 입력해주세요.")
