import asyncio
import websockets
import json

# 웹소켓 서버 포트 설정
WS_SERVER_PORT = 8000

connected_clients = {}
user_requests = {}

async def handler(websocket, path):
    async for message in websocket:
        data = json.loads(message)
        print("Received data:", data)

        if data["type"] == "register":
            user_id = data["user_id"]
            role = data["role"]
            if role not in connected_clients:
                connected_clients[role] = {}
            connected_clients[role][user_id] = websocket
            print(f"Registered {role} with ID {user_id}")

        elif data["type"] == "request":
            # 사용자 요청 처리
            user_id = data["user_id"]
            platform_from = data["platform_from"]
            platform_to = data["platform_to"]
            
            # 요청을 저장
            user_requests[user_id] = {
                "platform_from": platform_from,
                "platform_to": platform_to,
                "websocket": websocket
            }

            # 관리자에게 알림
            if "admin" in connected_clients:
                for admin_id, admin_ws in connected_clients["admin"].items():
                    await admin_ws.send(json.dumps({
                        "type": "new_request",
                        "user_id": user_id,
                        "platform_from": platform_from,
                        "platform_to": platform_to
                    }))

        elif data["type"] == "access_code":
            # 관리자가 엑세스 코드를 입력하면 사용자에게 전달
            user_id = data["user_id"]
            access_code = data["access_code"]
            platform = data["platform"]
            user_ws = user_requests[user_id]["websocket"]
            await user_ws.send(json.dumps({
                "type": "access_code",
                "platform": platform,
                "access_code": access_code
            }))

        elif data["type"] == "next_platform":
            # 관리자가 완료 버튼을 누르면 다음 플랫폼을 사용자에게 전달
            user_id = data["user_id"]
            user_data = user_requests[user_id]
            platform_to = user_data["platform_to"]

            if platform_to:
                next_platform = platform_to.pop(0)
                user_ws = user_requests[user_id]["websocket"]
                await user_ws.send(json.dumps({
                    "type": "next_platform",
                    "platform": next_platform
                }))
            else:
                user_ws = user_requests[user_id]["websocket"]
                await user_ws.send(json.dumps({
                    "type": "completion"
                }))

async def main():
    async with websockets.serve(handler, "0.0.0.0", WS_SERVER_PORT):
        await asyncio.Future()  # 서버가 종료되지 않도록 유지

asyncio.run(main())