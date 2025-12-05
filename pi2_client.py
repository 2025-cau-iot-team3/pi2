import asyncio
import websockets
import json
import os

from motor import move, motorInit
from sensor import sensor
from action.brain import Brain

global manual_control
manual_control = False
current_yolo_label = None
current_yolo_conf = 0.0
clients = {}

# [중요] Pi 2와 유선으로 연결된 IP 주소 입력
# (예: 크로스 케이블 연결 시 Pi 1의 고정 IP)
PI_1_IP = "192.168.0.137"
URI = f"ws://{PI_1_IP}:8000"

async def read_raw_data(file_path):
    try:
        with open(file_path, 'r') as f:
            return f.read().strip()
    except Exception as e:
        return None

def parse_sensor_json(sensor_json):
    try:
        data = json.loads(sensor_json)
        gyro = tuple(round(x * 10, 1) for x in data["gyro"])
        ultrasonic = [data["ultrasonic_1"], data["ultrasonic_2"]]
        return gyro, ultrasonic
    except Exception as e:
        return None, None

def run_brain(sensor):
    brain = Brain()
    left, right, emotion = brain.act(sensor)
    return left, right, emotion

async def brain_loop():
    freq = 2
    interval = 1.0 / freq

    while True:
        start_time = asyncio.get_event_loop().time()

        sensor_json = await read_raw_data("./sensor/sensor_state")
        gyro, ultrasonic = parse_sensor_json(sensor_json)
        obj = await read_raw_data("./action/yolo_obj")
        t = {"object": obj, "gyro": gyro, "distances": ultrasonic}

        left, right, emotion = run_brain(t)
        move.set_motor(left=left, right=right)

        print(f"\robj={obj}, gyro={gyro}, ultrasonic={ultrasonic} | brain: {left}, {right}, {emotion}", end="", flush=True)

        elapsed = asyncio.get_event_loop().time() - start_time
        sleep_time = max(0, interval - elapsed)
        await asyncio.sleep(sleep_time)

async def run_hardware_client():
    print(f"Pi 1 서버({URI})에 연결 시도 중...")

    async with websockets.connect(URI) as websocket:
        print("Pi 1 서버 연결 성공!")

        # 1. [등록] "나 Pi 1이야"라고 알림
        register_msg = {
            "command": "register",
            "payload": {"role": "pi2_hardware"}
        }
        await websocket.send(json.dumps(register_msg))
        print("등록 요청 전송 완료")

        # Start BrainRunner loop asynchronously
        asyncio.create_task(brain_loop())

        # 2. [수신 대기] 명령 기다림
        async for message in websocket:
            try:
                data = json.loads(message)
                cmd = data.get("command")
                payload = data.get("payload")

                # --- A. 모터 제어 명령 (from Pi 3) ---
                if cmd == "motor_control":
                    left = payload.get("left")
                    right = payload.get("right")
                    print(f"모터 구동: L={left}, R={right}")
                    # TODO: 실제 모터 드라이버 코드 연결
                    move.set_motor(left= left, right= right)

                # --- B. YOLO 결과 수신 (from Pi 2) ---
                elif cmd == "yolo_detection":
                    objects = payload.get("objects", [])
                    print(f"YOLO 감지됨! ({len(objects)}개)")
                    # for obj in objects:
                        # print(f"   - {obj['label']} ({obj['confidence']})")
                    # TODO: LCD에 표시하거나 스피커로 알림

                    # Save plain labels to action/yolo_obj (sorted by confidence desc)
                    try:
                        base_dir = os.path.dirname(os.path.abspath(__file__))
                        yolo_path = os.path.join(base_dir, "action", "yolo_obj")

                        # sort objects by confidence descending
                        sorted_objs = sorted(objects, key=lambda x: x.get("confidence", 0), reverse=True)

                        with open(yolo_path, "w") as f:
                            for obj_sorted in sorted_objs:
                                lbl = obj_sorted.get("label", "")
                                f.write(f"{lbl}\n")

                    except Exception as e:
                        print(f"[YOLO WRITE ERROR] {e}")
                                
                elif cmd == "sensor_update":
                    # 센서 상태 파일 저장
                    try:
                        base_dir = os.path.dirname(os.path.abspath(__file__))
                        sensor_path = os.path.join(base_dir, "sensor", "sensor_state")

                        with open(sensor_path, "w") as f:
                            json.dump(payload, f)

                    except Exception as e:
                        print(f"[SENSOR WRITE ERROR] {e}")

            except Exception as e:
                print(f"데이터 처리 에러: {e}")

if __name__ == "__main__":
    while True:
        try:
            asyncio.run(run_hardware_client())
        except Exception as e:
            print(f"연결 실패/끊김: {e}")
            import time
            time.sleep(3)

