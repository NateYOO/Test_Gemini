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
    
    if 'drink' in order:
        order['size'] = next((s for s, keywords in SIZE_KEYWORDS.items() if any(keyword in message for keyword in keywords)), None)
        order['temp'] = "ICE" if any(word in message for word in ["ice", "아이스", "차가운"]) else ("HOT" if any(word in message for word in ["hot", "따뜻한", "뜨거운"]) else None)
        order['options'] = [option for option in OPTIONS if option.lower() in message]
    
    return order

def get_missing_order_info(order: Dict) -> List[str]:
    missing = []
    if 'drink' not in order:
        missing.append("음료")
    if 'size' not in order or not order['size']:
        missing.append("사이즈")
    if 'temp' not in order or not order['temp']:
        missing.append("온도")
    return missing

def process_order(user_id: str, order: Dict) -> str:
    drink = order['drink']
    size = order['size']
    temp = order['temp']
    options = order.get('options', [])
    
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
            "paid": False,
            "payment_method": None,
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

def mark_order_as_paid(user_id: str, order_index: int) -> None:
    if user_id in st.session_state.orders and 0 <= order_index < len(st.session_state.orders[user_id]):
        st.session_state.orders[user_id][order_index]["paid"] = True
        update_order_history(user_id, order_index, {"paid": True})

def cancel_order(user_id: str, order_index: int) -> None:
    if user_id in st.session_state.orders and 0 <= order_index < len(st.session_state.orders[user_id]):
        del st.session_state.orders[user_id][order_index]
        remove_from_order_history(user_id, order_index)

def change_order_size(user_id: str, order_index: int, new_size: str) -> None:
    if user_id in st.session_state.orders and 0 <= order_index < len(st.session_state.orders[user_id]):
        order = st.session_state.orders[user_id][order_index]
        old_size = order['size']
        if old_size != new_size:
            price_difference = SIZES[new_size] - SIZES[old_size]
            order['size'] = new_size
            order['price'] += price_difference
            update_order_history(user_id, order_index, {"size": new_size, "price": order['price']})

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

def update_order_history(user_id: str, order_index: int, updates: Dict):
    history = load_order_history()
    if user_id in history and 0 <= order_index < len(history[user_id]):
        history[user_id][order_index].update(updates)
        save_order_history(history)

def remove_from_order_history(user_id: str, order_index: int):
    history = load_order_history()
    if user_id in history and 0 <= order_index < len(history[user_id]):
        del history[user_id][order_index]
        save_order_history(history)

def get_user_order_history(user_id: str) -> List[Dict]:
    history = load_order_history()
    return history.get(user_id, [])

# 새로 추가된 함수들
def get_bot_response(user_input: str) -> str:
    state = st.session_state.order_state
    
    if not state['drink']:
        drink = parse_drink(user_input)
        if drink:
            state['drink'] = drink
            return f"{drink} 좋은 선택이세요! {get_drink_description(drink)}\n\n{drink}를 어떻게 준비해 드릴까요?\n\n1. 온도: 따뜻하게 드시겠어요, 아니면 시원한 아이스로 준비해 드릴까요?"
        else:
            return "죄송합니다. 주문하신 음료를 이해하지 못했어요. 저희 메뉴에는 아메리카노, 카페라떼, 바닐라라떼, 카푸치노, 카라멜마키아또, 에스프레소 등이 있습니다. 어떤 음료를 드시고 싶으세요?"

    if not state['temp']:
        temp = parse_temperature(user_input)
        if temp:
            state['temp'] = temp
            return f"{temp} {state['drink']}로 준비하겠습니다.\n\n2. 사이즈: 레귤러 사이즈와 라지 사이즈 중 어떤 것으로 하시겠어요? (라지 사이즈는 500원 추가됩니다)"
        else:
            return "죄송합니다. 온도를 이해하지 못했어요. '따뜻하게' 또는 '차갑게'로 말씀해 주세요."

    if not state['size']:
        size = parse_size(user_input)
        if size:
            state['size'] = size
            return f"{size} 사이즈로 준비하겠습니다.\n\n3. 추가 옵션:\n   - 에스프레소 샷 추가 (500원)\n   - 휘핑크림 추가 (500원)\n   - 시럽 추가 (바닐라/헤이즐넛/카라멜, 각 500원)\n\n원하시는 옵션이 있다면 말씀해 주세요. 없으시다면 '옵션 없음'이라고 해주세요."
        else:
            return "죄송합니다. 사이즈를 이해하지 못했어요. '레귤러' 또는 '라지'로 말씀해 주세요."

    if not state['options']:
        options = parse_options(user_input)
        if options or user_input.lower() in ['옵션 없음', '없음']:
            state['options'] = options
            order_summary = f"{state['temp']} {state['size']} {state['drink']}"
            if options:
                order_summary += f" (옵션: {', '.join(options)})"
            return f"주문 내역을 확인해 드릴게요:\n{order_summary}\n\n이대로 주문하시겠어요? 맞으시면 '네', 수정하실 내용이 있다면 말씀해 주세요."
        else:
            return "죄송합니다. 옵션을 이해하지 못했어요. 원하시는 옵션을 정확히 말씀해 주시거나, 없으시면 '옵션 없음'이라고 말씀해 주세요."

    if not state['confirmed']:
        if '네' in user_input.lower():
            state['confirmed'] = True
            return "주문이 확인되었습니다. 결제 방법을 선택해 주세요. 현금, 카드, 모바일 결제 중 어떤 방법으로 하시겠어요?"
        else:
            return "주문을 변경하시겠어요? 어떤 부분을 수정할까요? (음료, 온도, 사이즈, 옵션 중 선택해 주세요)"

   if not state['payment_method']:
        payment_method = parse_payment_method(user_input)
        if payment_method:
            state['payment_method'] = payment_method
            order_result = process_order(st.session_state.current_user, state)
            st.session_state.order_state = {
                'drink': None, 'size': None, 'temp': None,
                'options': [], 'confirmed': False, 'payment_method': None
            }
            return f"{order_result}\n{payment_method}로 결제해 주셔서 감사합니다. 주문하신 음료를 곧 준비해 드리겠습니다!"
        else:
            return "죄송합니다. 결제 방법을 이해하지 못했어요. 현금, 카드, 모바일 중 하나로 말씀해 주세요."

    return "새로운 주문을 하시려면 음료 이름을 말씀해 주세요."

def get_drink_description(drink: str) -> str:
    descriptions = {
        "아메리카노": "깔끔하고 깊은 에스프레소의 풍미를 즐길 수 있는 클래식한 메뉴입니다.",
        "카페라떼": "부드러운 우유와 에스프레소의 조화로운 맛을 느낄 수 있는 대표적인 카페 메뉴입니다.",
        "바닐라라떼": "바닐라의 달콤한 향과 에스프레소의 풍미가 잘 어우러진 인기 메뉴입니다.",
        "카푸치노": "에스프레소와 스팀 밀크, 그리고 풍성한 우유 거품의 완벽한 밸런스를 자랑합니다.",
        "카라멜마키아또": "달콤한 카라멜과 에스프레소, 우유의 조화가 매력적인 디저트 같은 음료입니다.",
        "에스프레소": "진한 커피의 맛과 향을 온전히 즐길 수 있는 커피 본연의 맛입니다."
    }
    return descriptions.get(drink, "저희 카페의 특별한 메뉴입니다.")

# 추가적인 파싱 함수들
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
    if any(word in input.lower() for word in SIZE_KEYWORDS["Large"]):
        return "Large"
    elif any(word in input.lower() for word in SIZE_KEYWORDS["Regular"]):
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

# 세션 상태 초기화
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
if 'order_state' not in st.session_state:
    st.session_state.order_state = {
        'drink': None,
        'size': None,
        'temp': None,
        'options': [],
        'confirmed': False,
        'payment_method': None
    }

# 메인 애플리케이션
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
