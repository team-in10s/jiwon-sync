import streamlit as st
import websockets
import asyncio
import json
import nest_asyncio
from datetime import datetime

# 웹소켓 URL 설정
WS_SERVER_URL = "ws://jiwon-sync.in10s.co:8000"
# WS_SERVER_URL = "ws://localhost:8000"


# URL 파라미터로부터 연락처를 받아옴
user_id = st.query_params["user_id"]

# 기존 이벤트 루프에 nest_asyncio 적용
nest_asyncio.apply()

# Streamlit UI 구성
st.title("지원전에 Sync")

# 종단간 암호화 및 RBI 기술 설명
st.markdown("""
- 관련 질문이 있으신 경우, 고객센터로 문의주시면, 최대한 빠르게 답변해드립니다.
- 고객센터(카카오톡) : http://pf.kakao.com/_xjxkJbG/chat
---
## 보안 및 개인정보 보호

지원전에 팀은 여러분의 개인정보를 소중히 다루며, 안전한 데이터 전송을 위해 다음과 같은 보안 기술을 적용하고 있습니다:

#### 종단간 암호화
- 데이터 전송 과정에서 주고받는 모든 데이터는 종단간 암호화(E2EE)를 통해 보호됩니다. 이는 중간에서 데이터가 도청되거나 변조되는 것을 방지합니다.

#### 원격 브라우저 격리(RBI)
- RBI 기술을 통해 브라우저 세션이 사용자와 분리된 환경에서 안전하게 실행됩니다. 이는 브라우저를 통한 공격을 방지하고, 사용자의 시스템을 보호합니다.
안심하고 서비스를 이용해주세요.
---
""")

st.markdown("""
##### 1. 동기화를 위한 사이트를 선택해주세요.
""")

# 이력서를 가져올 플랫폼 선택
platform_from = st.selectbox("이력서를 가져올 플랫폼", ["사람인", "잡코리아", "인크루트", "원티드", "리멤버", "점핏", "링크드인"])

# 이력서를 보낼 플랫폼 선택
platform_to = st.multiselect("이력서를 보낼 플랫폼", ["사람인", "잡코리아", "인크루트", "원티드", "리멤버", "점핏", "링크드인"])

async def send_data():
    try:
        async with websockets.connect(WS_SERVER_URL) as websocket:
            await websocket.send(json.dumps({"type": "register", "user_id": user_id, "role": "user"}))

            data = {
                "type": "request",
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "platform_from": platform_from,
                "platform_to": platform_to
            }
            await websocket.send(json.dumps(data))

            while True:
                response = await websocket.recv()
                response_data = json.loads(response)

                if response_data["type"] == "access_code":
                    platform = response_data["platform"]
                    access_code = response_data["access_code"]
                    st.markdown(f"### {platform} 엑세스 코드: {access_code}")
                    st.success(f"{platform}에 엑세스 코드를 입력하여 로그인해주세요.")
                    
                    if st.button("엑세스 코드 재요청",f"rerequest_{platform}"):
                        await websocket.send(json.dumps({
                            "type": "access_code_request",
                            "user_id": user_id,
                            "platform": platform
                        }))
                        st.success("엑세스 코드 재요청이 관리자에게 전달되었습니다.")
                
                elif response_data["type"] == "login_complete":
                    st.markdown("""
                    <script>
                    alert("로그인이 완료되었습니다. 잠시 후 연결이 종료됩니다.");
                    </script>
                    """, unsafe_allow_html=True)
                    await asyncio.sleep(5)
                    break
                
                elif response_data["type"] == "completion":
                    st.markdown("""
                    ##### 24시간 이내에 지원서류 동기화가 완료됩니다.

                    - 원격지원 신청 이후, 별도 로그아웃 하시면 서류 동기화 작업이 진행되지 않습니다.
                    - 동기화가 완료되면 문자 메시지로 발송됩니다.

                    관련 질문이 있으신 경우, 고객센터로 문의주시면, 최대한 빠르게 답변해드립니다.

                    고객센터(카카오톡) : [고객센터 링크](http://pf.kakao.com/_xjxkJbG/chat)

                    감사합니다.
                    """)
                    break
                
    except websockets.ConnectionClosedError as e:
        st.error("접속 오류가 발생했습니다. 반드시 PC와 Chrome 브라우저를 이용해주시고, 사용자가 많아 잠시 후 다시 시도해주세요.")

def start_sync():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(send_data())

if st.button("동기화 시작"):
    if platform_from and platform_to:
        st.markdown("### 3. 아래 링크로 이동하여 각 플랫폼에 대한 엑세스 코드를 입력해주세요.")
        st.markdown("[Google Remote Desktop 링크](https://remotedesktop.google.com/support)")
        st.markdown("""
        - 반드시 PC와 Chrome 브라우저를 이용해주세요.
        - Google Remote Desktop 설치가 필요하지 않습니다. 링크로 이동 후 엑세스 코드만 입력하시면 됩니다.
        """)
        start_sync()
    else:
        st.error("모든 필드를 입력해주세요.")