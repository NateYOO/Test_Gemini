import streamlit as st
import google.generativeai as genai
from typing import List, Tuple, Dict
from datetime import datetime

# Streamlit 페이지 설정
st.set_page_config(page_title="Barista Bot", page_icon="☕", layout="wide")

# Gemini API 설정
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("GOOGLE_API_KEY not found in Streamlit secrets. Please set it up.")
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

# 메뉴 및 가격 정보
MENU = {
    "Coffee Drinks": {
        "Americano": {"price": 4500, "options": ["HOT", "ICE"]},
        "Cafe Latte": {"price": 5000, "options": ["HOT", "ICE"]},
        "Vanilla Latte": {"price": 5500, "options": ["HOT", "ICE"]},
        "Cappuccino": {"price": 5000, "options": ["HOT"]},
        "Caramel Macchiato": {"price": 5500, "options": ["HOT", "ICE"]},
        "Espresso": {"price": 3000, "options": ["HOT"]},
    },
    "Non-Coffee Drinks": {
        "Green Tea Latte": {"price": 5500, "options": ["HOT", "ICE"]},
        "Hot Chocolate": {"price": 5000, "options": ["HOT", "ICE"]},
        "Yuzu Tea": {"price": 5000, "options": ["HOT", "ICE"]},
        "Chamomile Tea": {"price": 4500, "options": ["HOT"]},
        "Peppermint Tea": {"price": 4500, "options": ["HOT"]},
    }
}

SIZES = {"Regular": 0, "Large": 500}
OPTIONS = {
    "Extra shot": 500,
    "Whipped cream": 500,
    "Vanilla syrup": 500,
    "Hazelnut syrup": 500,
    "Caramel syrup": 500
}

# 주문 및 사용자 관리 함수
def add_to_order(user_id: str, drink: str, size: str, options: List[str]) -> None:
    if user_id not in st.session_state.orders:
        st.session_state.orders[user_id] = []
    
    category = next((cat for cat, drinks in MENU.items() if drink in drinks), None)
    if category:
        base_price = MENU[category][drink]["price"]
        size_price = SIZES[size]
        options_price = sum(OPTIONS[option] for option in options if option in OPTIONS)
        total_price = base_price + size_price + options_price

        st.session_state.orders[user_id].append({
            "drink": drink,
            "size": size,
            "options": options,
            "price": total_price,
            "paid": False,
            "timestamp": datetime.now()
        })

def get_user_orders(user_id: str) -> List[Dict]:
    return st.session_state.orders.get(user_id, [])

def calculate_daily_sales() -> int:
    return sum(order["price"] for user_orders in st.session_state.orders.values() for order in user_orders if order["paid"])

def mark_order_as_paid(user_id: str, order_index: int) -> None:
    if user_id in st.session_state.orders and 0 <= order_index < len(st.session_state.orders[user_id]):
        st.session_state.orders[user_id][order_index]["paid"] = True

# Gemini 모델 설정
model = genai.GenerativeModel('gemini-1.0-pro')

# 세션 상태 초기화
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'orders' not in st.session_state:
    st.session_state.orders = {}
if 'current_user' not in st.session_state:
    st.session_state.current_user = "user1"  # 기본 사용자
if 'convo' not in st.session_state:
    st.session_state.convo = model.start_chat(history=[
        {'role': 'user', 'parts': [COFFEE_BOT_PROMPT]},
        {'role': 'model', 'parts': ['Understood. I'm ready to take orders!']}
    ])

# 메뉴판 표시 함수
def display_menu():
    st.header("☕ Our Menu")
    for category, items in MENU.items():
        st.subheader(category)
        for item, details in items.items():
            price = details['price']
            options = ', '.join(details['options'])
            st.write(f"- {item}: {price} won ({options})")
    
    st.subheader("Sizes")
    for size, price in SIZES.items():
        st.write(f"- {size}: +{price} won")
    
    st.subheader("Additional Options")
    for option, price in OPTIONS.items():
        st.write(f"- {option}: +{price} won")

# 레이아웃
col1, col2 = st.columns([2, 1])

with col1:
    st.title("☕ Barista Bot")
    
    # 메뉴 표시 토글
    show_menu = st.checkbox("Show Menu")
    if show_menu:
        display_menu()
    
    st.write("Welcome! What would you like to order?")

    # 채팅 메시지 표시
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 사용자 입력
    if prompt := st.chat_input("What's your order?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 봇 응답
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            for response in st.session_state.convo.send_message(prompt, stream=True):
                full_response += response.text
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
        
        st.session_state.messages.append({"role": "assistant", "content": full_response})

        # 여기에 주문 처리 로직 추가 (예: 메시지 분석 후 add_to_order 호출)

with col2:
    st.sidebar.title("Order Management")
    
    # 사용자 선택
    st.sidebar.selectbox("Select User", ["user1", "user2", "user3"], key="current_user")

    # 현재 주문 상태 표시
    st.sidebar.header(f"Current Orders for {st.session_state.current_user}")
    user_orders = get_user_orders(st.session_state.current_user)
    for idx, order in enumerate(user_orders):
        st.sidebar.write(f"{idx + 1}. {order['drink']} ({order['size']})")
        st.sidebar.write(f"   Options: {', '.join(order['options'])}")
        st.sidebar.write(f"   Price: {order['price']} won")
        st.sidebar.write(f"   Paid: {'Yes' if order['paid'] else 'No'}")
        if not order['paid']:
            if st.sidebar.button(f"Mark as Paid (Order {idx + 1})"):
                mark_order_as_paid(st.session_state.current_user, idx)
                st.experimental_rerun()

    # 일일 매출 계산
    daily_sales = calculate_daily_sales()
    st.sidebar.header("Daily Sales")
    st.sidebar.write(f"Total: {daily_sales} won")

    # 새 주문 시작 버튼
    if st.sidebar.button("Start New Order"):
        st.session_state.messages = []
        st.experimental_rerun()
