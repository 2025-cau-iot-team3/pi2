# server.py  (Pi2 하드웨어 서버)
import asyncio
import websockets
import json

from motor import move, motorInit
from sensor import sensor
from action import brain

global manual_control
manual_control = False
current_yolo_label = None
current_yolo_conf = 0.0
clients = {}

async def keep_thinking():
    
    value = sensor.read()
    global current_yolo_label, current_yolo_conf
    t = {
        "object": current_yolo_label,
        "confidence": current_yolo_conf,
        "gyro": value["gyro"],
        "distances": value["distances"]
    }
    if not manual_control: 
        left, right, emotion = brain.think(sensor= t)
        move.set_motor(left= left, right= right)
        print(left, right, emotion)

async def handle_client(websocket):
    # First message must be register
    register_msg = json.loads(await websocket.recv())
    cid = register_msg.get("payload", {}).get("id", "unknown")
    clients[cid] = websocket
    print(f"[등록됨] id={cid}")

    print("새 클라이언트 연결!")

    try:
        async for msg in websocket:
            data = json.loads(msg)
            cmd = data.get("command")
            payload = data.get("payload", {})

            print(f"[수신] cmd={cmd}, payload={payload}")

            # === motor_control ===
            if cmd == "motor_control":
                global manual_control
                manual_control = True
                left = payload.get("left", 0)
                right = payload.get("right", 0)
                print(f"[컨트롤] L: {left}, R: {right}")
                # TODO: 실제 모터 동작 연결
                move.set_motor(left= left, right= right)
            
            elif cmd == "stop_control":
                move.set_motor(left=0, right=0)
                manual_control = False
                print("[컨트롤] 수동 컨트롤 종료. 이제 자유롭게 움직입니다.")

            # === yolo_detection ===
            elif cmd == "yolo_detection":
                obj = payload.get("label", 0)
                conf = payload.get("confidence", 0)
                print(f"[YOLO] from {cid} 객체: {obj}, 신뢰도: {conf}")
                global current_yolo_label, current_yolo_conf
                current_yolo_label = obj
                current_yolo_conf = conf
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
    
    async def thinking_loop():
        while True:
            await keep_thinking()
            await asyncio.sleep(1)

    server = websockets.serve(handle_client, "0.0.0.0", 8000)

    await asyncio.gather(
        server,
        thinking_loop()
    )
        
async def quit():
    motorInit.kill_process("move_daemon")
    motorInit.kill_process("pigpiod")
    print("서버 종료 완료.")

if __name__ == "__main__":
    try:
        motorInit.init()
        asyncio.run(main())
    except KeyboardInterrupt:
        asyncio.run(quit())