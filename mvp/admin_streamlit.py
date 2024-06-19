import streamlit as st
import websockets
import asyncio
import json
import nest_asyncio
from urllib.parse import urlparse, parse_qs

# 웹소켓 URL 설정
WS_SERVER_URL = "ws://jiwon-sync.in10s.co:8000"
# WS_SERVER_URL = "ws://localhost:8000"

# URL 파라미터로부터 연락처를 받아옴
admin_id = st.query_params["admin_id"]

# 기존 이벤트 루프에 nest_asyncio 적용
nest_asyncio.apply()

# Streamlit UI 구성
st.title("관리자 페이지")

# 새로운 사용자 요청을 실시간으로 확인
st.markdown("### 새로운 사용자 요청")

# 상태 초기화
if "current_request" not in st.session_state:
    st.session_state.current_request = None
if "next_platform" not in st.session_state:
    st.session_state.next_platform = None
if "websocket" not in st.session_state:
    st.session_state.websocket = None
if "remaining_platforms" not in st.session_state:
    st.session_state.remaining_platforms = []

async def listen_for_requests():
    async with websockets.connect(WS_SERVER_URL) as websocket:
        st.session_state.websocket = websocket
        await websocket.send(json.dumps({"type": "register", "role": "admin", "user_id": admin_id}))

        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)

                if data["type"] == "new_request":
                    st.session_state.current_request = {
                        "user_id": data["user_id"],
                        "platform_from": data["platform_from"],
                        "platform_to": data["platform_to"]
                    }
                    st.session_state.remaining_platforms = [data["platform_from"]] + data["platform_to"]
                    st.session_state.next_platform = st.session_state.remaining_platforms.pop(0)
                    st.audio('https://www.soundjay.com/buttons/sounds/button-14.mp3', format="audio/mp3", autoplay=True)
                    st.experimental_rerun()
                
                elif data["type"] == "access_code_request":
                    st.session_state.next_platform = data["platform"]
                    st.experimental_rerun()
            except websockets.ConnectionClosed:
                st.session_state.websocket = None
                st.error("웹소켓 연결이 닫혔습니다. 실시간 수신을 다시 시작해주세요.")
                break

async def send_access_code(user_id, platform, access_code):
    if st.session_state.websocket and access_code.strip():
        await st.session_state.websocket.send(json.dumps({
            "type": "access_code",
            "user_id": user_id,
            "platform": platform,
            "access_code": access_code
        }))

async def send_next_platform(user_id):
    if st.session_state.websocket:
        if st.session_state.remaining_platforms:
            st.session_state.next_platform = st.session_state.remaining_platforms.pop(0)
            await st.session_state.websocket.send(json.dumps({
                "type": "next_platform",
                "user_id": user_id,
                "platform": st.session_state.next_platform
            }))
        else:
            await st.session_state.websocket.send(json.dumps({
                "type": "completion",
                "user_id": user_id
            }))
            # st.session_state.current_request = None
            # st.session_state.next_platform = None
            # st.session_state.remaining_platforms = []
            # st.experimental_rerun()

async def send_login_complete(user_id):
    if st.session_state.websocket:
        await st.session_state.websocket.send(json.dumps({
            "type": "login_complete",
            "user_id": user_id
        }))

def start_listening():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(listen_for_requests())

# 실시간 수신 시작 버튼
if st.button("실시간 수신 시작"):
    start_listening()

# 사용자 요청 처리
if st.session_state.current_request:
    user_id = st.session_state.current_request["user_id"]
    platform_from = st.session_state.current_request["platform_from"]
    platform_to = st.session_state.current_request["platform_to"]
    next_platform = st.session_state.next_platform

    st.write(f"사용자 ID: {user_id}")
    st.write(f"가져올 플랫폼: {platform_from}")
    st.write(f"보낼 플랫폼: {', '.join(platform_to)}")
    st.write(f"현재 진행할 플랫폼: {next_platform}")

    access_code = st.text_input(f"{next_platform} 엑세스 코드 입력:")

    if st.button("엑세스 코드 전송"):
        if access_code.strip():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(send_access_code(user_id, next_platform, access_code))
            st.success(f"{next_platform}에 대한 엑세스 코드가 전송되었습니다.")
        else:
            st.error("엑세스 코드는 비어 있을 수 없습니다.")

    if st.button("로그인 완료"):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(send_login_complete(user_id))
        loop.run_until_complete(send_next_platform(user_id))
        st.success(f"{next_platform} 플랫폼의 로그인이 완료되었습니다. 다음 플랫폼으로 이동합니다.")