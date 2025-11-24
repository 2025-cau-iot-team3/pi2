# test.py
# 로봇 감정 판단 및 모터 출력 테스트 스크립트

import sys
from brain import Brain

def run_single_test(sensor_input):
    brain = Brain()
    left, right, emotion = brain.act(sensor_input)

    print("=== 테스트 결과 ===")
    print(f"입력: {sensor_input}")
    print(f"감정: {emotion}")
    print(f"모터: L={left}, R={right}")
    print("==================\n")


def run_all_tests():
    test_cases = [
        # gyro 기준 dizzy
        {"gyro": (60, 10, 5), "distances": [100, 150], "object": "dog"},

        # 거리 두 번째 값 기준 scary
        {"gyro": (10, 10, 10), "distances": [120, 250], "object": "dog"},

        # 위험 물체 scary
        {"gyro": (10, 10, 10), "distances": [80, 90], "object": "knife"},

        # 좋아하는 물체 happy
        {"gyro": (10, 10, 20), "distances": [120, 150], "object": "dog"},
        {"gyro": (20, 10, 10), "distances": [90, 100], "object": "cat"},
        {"gyro": (30, 20, 10), "distances": [150, 150], "object": "person"},

        # 거리 조건 happy → scary 테스트
        {"gyro": (10, 10, 10), "distances": [80, 210], "object": "dog"},

        # neutral
        {"gyro": (0, 0, 0), "distances": [50, 60], "object": ""},
        {"gyro": (10, 20, 10), "distances": [120, 150], "object": "tree"},
    ]

    for case in test_cases:
        run_single_test(case)


if __name__ == "__main__":

    # 센서 값을 CLI에서 직접 입력하는 모드
    if len(sys.argv) > 1 and sys.argv[1] == "--manual":
        # 예: python test.py --manual dog 10 20 30 100 150
        obj = sys.argv[2]
        gx = float(sys.argv[3])
        gy = float(sys.argv[4])
        gz = float(sys.argv[5])
        d1 = float(sys.argv[6])
        d2 = float(sys.argv[7])

        sensor = {
            "object": obj,
            "gyro": (gx, gy, gz),
            "distances": [d1, d2],
        }
        run_single_test(sensor)
    else:
        # 기본은 전체 테스트 실행
        run_all_tests()