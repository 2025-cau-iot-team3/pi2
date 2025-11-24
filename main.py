# ws_server.py
import asyncio
import websockets
import json

# 접속한 장치들 저장
connected_clients = {}

async def handle_client(websocket, path):
    print("새 연결 감지!")

    try:
        async for message in websocket:
            data = json.loads(message)
            cmd = data.get("command")
            payload = data.get("payload")

            # 1. 장치 등록(register)
            if cmd == "register":
                role = payload.get("role", "unknown")
                connected_clients[role] = websocket
                print(f"[등록 완료] role={role}")

            # 2. Pi 3 → Pi 2 모터 제어 전달
            elif cmd == "motor_control":
                if "pi2_hardware" in connected_clients:
                    await connected_clients["pi2_hardware"].send(json.dumps(data))
                    print("[전달 완료] motor_control → pi2_hardware")

            # 3. Pi 2 → Pi 3 YOLO 감지 전달
            elif cmd == "yolo_detection":
                if "pi3_brain" in connected_clients:
                    await connected_clients["pi3_brain"].send(json.dumps(data))
                    print("[전달 완료] yolo_detection → pi3_brain")

    except Exception as e:
        print(f"클라이언트 처리 에러: {e}")

    finally:
        # 연결 종료 시 connected_clients에서 제거
        to_remove = [k for k,v in connected_clients.items() if v == websocket]
        for key in to_remove:
            del connected_clients[key]
        print("클라이언트 연결 종료")


async def main():
    print("웹소켓 서버 시작 ws://0.0.0.0:8000")
    async with websockets.serve(handle_client, "0.0.0.0", 8000):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())