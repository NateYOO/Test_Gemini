import streamlit as st
import google.generativeai as genai
from typing import List, Dict
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

# 세션 상태 초기화
if 'order_state' not in st.session_state:
    st.session_state.order_state = {
        'drink': None,
        'size': None,
        'temp': None,
        'options': [],
        'confirmed': False,
        'payment_method': None
    }
if 'orders' not in st.session_state:
    st.session_state.orders = {}
if 'current_user' not in st.session_state:
    st.session_state.current_user = "user1"

# 주문 및 사용자 관리 함수
def process_order(user_id: str, order_state: Dict) -> str:
    drink = order_state['drink']
    size = order_state['size']
    temp = order_state['temp']
    options = order_state['options']
    
    category = next((cat for cat, items in MENU.items() if drink in items), None)
    if category:
        base_price = MENU[category][drink]["price"]
        size_price = SIZES[size]
        options_price = sum(OPTIONS[option] for option in options if option in OPTIONS)
        total_price = base_price + size_price + options_price

        new_order = {
            "drink": drink,
            "size": size,
            "temp": temp,
            "options": options,
            "price": total_price,
            "paid": True,
            "payment_method": order_state['payment_method'],
            "timestamp": datetime.now().isoformat()
        }
        
        if user_id not in st.session_state.orders:
            st.session_state.orders[user_id] = []
        st.session_state.orders[user_id].append(new_order)
        add_to_order_history(user_id, new_order)

        return f"{drink} ({size}, {temp}) 주문이 완료되었습니다. 가격: {total_price}원"
    return "주문 처리 중 오류가 발생했습니다."

def get_user_orders(user_id: str) -> List[Dict]:
    return st.session_state.orders.get(user_id, [])

def calculate_daily_sales() -> int:
    return sum(order["price"] for user_orders in st.session_state.orders.values() for order in user_orders if order["paid"])

def cancel_order(user_id: str, order_index: int) -> None:
    if user_id in st.session_state.orders and 0 <= order_index < len(st.session_state.orders[user_id]):
        del st.session_state.orders[user_id][order_index]
        remove_from_order_history(user_id, order_index)

# 주문 히스토리 관리 함수
def load_order_history():
    try:
        with open("order_history.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_order_history(history):
    with open("order_history.json", "w") as f:
        json.dump(history, f)

def add_to_order_history(user_id: str, order: Dict):
    history = load_order_history()
    if user_id not in history:
        history[user_id] = []
    history[user_id].append(order)
    save_order_history(history)

def remove_from_order_history(user_id: str, order_index: int):
    history = load_order_history()
    if user_id in history and 0 <= order_index < len(history[user_id]):
        del history[user_id][order_index]
        save_order_history(history)

def get_user_order_history(user_id: str) -> List[Dict]:
    history = load_order_history()
    return history.get(user_id, [])

# 대화 관리 및 주문 처리 함수
def get_bot_response(user_input: str) -> str:
    state = st.session_state.order_state
    
    if not state['drink']:
        drink = parse_drink(user_input)
        if drink:
            state['drink'] = drink
            return f"{drink} 좋은 선택이에요. 따뜻하게 드릴까요, 아니면 시원하게 아이스로 준비할까요?"
        else:
            return "죄송합니다. 주문하신 음료를 이해하지 못했어요. 메뉴에 있는 음료를 말씀해 주시겠어요?"

    elif not state['temp']:
        temp = parse_temperature(user_input)
        if temp:
            state['temp'] = temp
            return f"{temp} {state['drink']}로 준비하겠습니다. 사이즈는 어떻게 해드릴까요? 레귤러와 라지 중 선택하실 수 있어요."
        else:
            return "죄송합니다. 온도를 이해하지 못했어요. '따뜻하게' 또는 '차갑게'로 말씀해 주세요."

    elif not state['size']:
        size = parse_size(user_input)
        if size:
            state['size'] = size
            return f"{size} 사이즈로 준비하겠습니다. 혹시 샷 추가나 시럽 추가 같은 옵션을 원하시나요?"
        else:
            return "죄송합니다. 사이즈를 이해하지 못했어요. '레귤러' 또는 '라지'로 말씀해 주세요."

    elif not state['confirmed']:
        options = parse_options(user_input)
        if options:
            state['options'].extend(options)
        
        order_summary = f"{state['temp']} {state['size']} {state['drink']}"
        if state['options']:
            order_summary += f" (옵션: {', '.join(state['options'])})"
        
        state['confirmed'] = True
        return f"주문 내역을 확인해 드릴게요: {order_summary}. 맞으신가요? 결제를 진행하시려면 '네'라고 말씀해 주세요."

    elif not state['payment_method']:
        if '네' in user_input.lower():
            return "결제 방법을 선택해 주세요. 현금, 카드, 모바일 중 어떤 방법으로 하시겠어요?"
        else:
            state['confirmed'] = False
            return "주문을 변경하시겠어요? 어떤 부분을 수정할까요?"

    else:
        payment_method = parse_payment_method(user_input)
        if payment_method:
            state['payment_method'] = payment_method
            order_result = process_order(st.session_state.current_user, state)
            st.session_state.order_state = {
                'drink': None, 'size': None, 'temp': None,
                'options': [], 'confirmed': False, 'payment_method': None
            }
            return f"{order_result} {payment_method}로 결제해 주셔서 감사합니다. 주문하신 음료를 곧 준비해 드리겠습니다!"
        else:
            return "죄송합니다. 결제 방법을 이해하지 못했어요. 현금, 카드, 모바일 중 하나로 말씀해 주세요."

# 파싱 함수들
def parse_drink(input: str) -> str:
    input = input.lower()
    for category in MENU.values():
        for drink in category.keys():
            if drink.lower() in input:
                return drink
    return None

def parse_temperature(input: str) -> str:
    if any(word in input.lower() for word in ["따뜻", "뜨겁", "핫"]):
        return "HOT"
    elif any(word in input.lower() for word in ["차갑", "시원", "아이스"]):
        return "ICE"
    return None

def parse_size(input: str) -> str:
    if any(word in input.lower() for word in ["큰", "라지", "large"]):
        return "Large"
    elif any(word in input.lower() for word in ["작은", "레귤러", "regular"]):
        return "Regular"
    return None

def parse_options(input: str) -> List[str]:
    return [option for option in OPTIONS.keys() if option.lower() in input.lower()]

def parse_payment_method(input: str) -> str:
    if "현금" in input:
        return "현금"
    elif "카드" in input:
        return "카드"
    elif "모바일" in input:
        return "모바일"
    return None

# 메뉴 표시 함수
def display_menu():
    st.header("☕ 메뉴판")
    for category, items in MENU.items():
        st.subheader(category)
        for item, details in items.items():
            price = details['price']
            options = ', '.join(details['options'])
            st.write(f"- {item}: {price}원 ({options})")
    
    st.subheader("사이즈")
    for size, price in SIZES.items():
        st.write(f"- {size}: +{price}원")
    
    st.subheader("추가 옵션")
    for option, price in OPTIONS.items():
        st.write(f"- {option}: +{price}원")

# 메인 애플리케이션
st.title("☕ 바리스타 봇")

# 메뉴 표시 토글
if st.checkbox("메뉴 보기"):
    display_menu()

# 채팅 인터페이스
chat_container = st.container()

# 사용자 입력
user_input = st.chat_input("주문을 입력해주세요.")

if user_input:
    st.chat_message("user").write(user_input)
    bot_response = get_bot_response(user_input)
    st.chat_message("assistant").write(bot_response)

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
        
        if st.button(f"주문 취소 (주문 {idx + 1})"):
            cancel_order(st.session_state.current_user, idx)
            st.success(f"주문 {idx + 1}이 취소되었습니다.")
            st.experimental_rerun()

    st.header("일일 매출")
    st.write(f"총액: {calculate_daily_sales()}원")

    if st.button("새 주문 시작"):
        st.session_state.order_state = {
            'drink': None, 'size': None, 'temp': None,
            'options': [], 'confirmed': False, 'payment_method': None
        }
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

if __name__ == "__main__":
    st.write("바리스타 봇이 실행 중입니다. 주문을 입력해주세요.")
