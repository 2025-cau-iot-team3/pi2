# server.py  (Pi2 하드웨어 서버)
import asyncio
import websockets
import json

import motor

async def handle_client(websocket):
    print("새 클라이언트 연결!")

    try:
        async for msg in websocket:
            data = json.loads(msg)
            cmd = data.get("command")
            payload = data.get("payload", {})

            print(f"[수신] cmd={cmd}, payload={payload}")

            # === motor_control ===
            if cmd == "motor_control":
                left = payload.get("left", 0)
                right = payload.get("right", 0)
                print(f"[모터 제어] L={left}, R={right}")
                # TODO: 실제 모터 동작 연결
                motor.move.set_motor(left= left, right= right)

            # === yolo_detection ===
            elif cmd == "yolo_detection":
                print(f"[YOLO] 객체 감지됨: {payload}")
                # TODO: LCD 표시 / 소리 등

            # === sensor_request (optional) ===
            elif cmd == "sensor_request":
                # Pi2가 sensor 값을 서버로 전송하고 싶을 때 사용
                pass

    except Exception as e:
        print("에러:", e)

    finally:
        print("클라이언트 연결 종료")


async def main():
    print("Pi2 서버 시작: ws://0.0.0.0:8000")
    async with websockets.serve(handle_client, "0.0.0.0", 8000):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
    motor.motorInit()