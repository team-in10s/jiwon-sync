import asyncio
import websockets
import json

clients = {}

async def register(websocket, role, user_id):
    clients[user_id] = {"websocket": websocket, "role": role}
    print(f"{role.capitalize()} {user_id} connected.")

async def unregister(user_id):
    if user_id in clients:
        del clients[user_id]
        print(f"User {user_id} disconnected.")

async def handler(websocket, path):
    try:
        message = await websocket.recv()
        data = json.loads(message)
        
        if data["type"] == "register":
            await register(websocket, data["role"], data["user_id"])

        while True:
            message = await websocket.recv()
            data = json.loads(message)
            if data["type"] in ["access_code", "next_platform", "completion", "login_complete"]:
                user_id = data["user_id"]
                if user_id in clients:
                    await clients[user_id]["websocket"].send(message)
            elif data["type"] == "access_code_request":
                admin_id = data["admin_id"]
                if admin_id in clients:
                    await clients[admin_id]["websocket"].send(message)

    except websockets.ConnectionClosed:
        await unregister(data["user_id"])

start_server = websockets.serve(handler, "0.0.0.0", 8080)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()