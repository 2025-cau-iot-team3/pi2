# sensor.py

import json
import os
import time

SENSOR_STATE_PATH = os.path.expanduser("~/pi2/sensor/sensor_state")

def read():
    """
    sensor_state 파일을 읽어 dict로 반환.
    파일 없거나 파싱 실패 시 안전한 dummy 값 반환.
    """
    try:
        with open(SENSOR_STATE_PATH, "r") as f:
            data = json.load(f)

        ultrasonic_1 = float(data.get("ultrasonic_1", -1.0))
        ultrasonic_2 = float(data.get("ultrasonic_2", -1.0))
        gyro_list = data.get("gyro", [0.0, 0.0, 0.0])
        gyro = tuple(gyro_list)
        ts = data.get("ts", int(time.time()))

        # 구조 통일해서 반환
        return {
            "distances": [ultrasonic_1, ultrasonic_2],
            "gyro": gyro,
            "ts": ts
        }

    except Exception as e:
        print(f"[sensor] Read error: {e}")

        # 실패 시 기본 dummy 반환
        return {
            "distances": [-1.0, -1.0],
            "gyro": (0.0, 0.0, 0.0),
            "ts": int(time.time())
        }


if __name__ == "__main__":
    print(read())