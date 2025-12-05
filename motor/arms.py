#!/usr/bin/env python3
import sys
import time
import argparse

SERVO_CMD_PATH = "/home/iot/pi2/motor/servo_cmd"

# ---------------------------------------------------------
# -90 ~ 90 입력 → 0 ~ 180 정규화
# ---------------------------------------------------------
def normalize_angle(a):
    if a < -90:  a = -90
    if a > 90:   a = 90
    return a + 90

# ---------------------------------------------------------
# servo_cmd 파일로 명령 전송
# ---------------------------------------------------------
def send_servo(left_raw, right_raw, delay=0.15):
    left  = normalize_angle(left_raw)
    right = normalize_angle(right_raw)

    cmd = f"{left} {right}"
    try:
        with open(SERVO_CMD_PATH, "w") as f:
            f.write(cmd)
    except Exception as e:
        print("[ERROR] servo_cmd 쓰기 실패:", e)
        return

    print(f"[CMD] RAW({left_raw},{right_raw}) → MAP({left},{right})")
    time.sleep(delay)

# ---------------------------------------------------------
# 감정 모션
# ---------------------------------------------------------
def motion_happy():
    print("[INFO] HAPPY 모션 시작")
    down = -30
    up   =  50

    send_servo(down, down)
    for i in range(2):
        send_servo(up, up)
        send_servo(down, down)

    send_servo(0, 0, delay=0.4)

def motion_sad():
    print("[INFO] SAD 모션 시작")
    down = -50
    send_servo(down, down)
    time.sleep(3)
    send_servo(0, 0, delay=0.4)

def motion_surprised():
    print("[INFO] SURPRISED 모션 시작")
    up = 60
    send_servo(up, up)
    time.sleep(3)
    send_servo(0, 0, delay=0.4)

# ---------------------------------------------------------
# 메인
# ---------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-emo", "--emotion", type=str,
                        help="happy / sad / surprised / all")

    parser.add_argument("-set", "--set_angles", nargs=2, type=int,
                        metavar=('LEFT', 'RIGHT'),
                        help="사용자 각도 입력(-90 ~ +90)")

    args = parser.parse_args()

    # ---- SET MODE ----
    if args.set_angles:
        L_raw = args.set_angles[0]
        R_raw = args.set_angles[1]

        print(f"[INFO] 수동 세팅: LEFT={L_raw}, RIGHT={R_raw}")
        send_servo(L_raw, R_raw)
        sys.exit(0)

    # ---- EMOTION MODE ----
    if args.emotion:
        emo = args.emotion.lower()
        print(f"[INFO] 선택 감정: {emo}")

        if emo == "happy":
            motion_happy()

        elif emo == "sad":
            motion_sad()

        elif emo in ("surprised", "surprise"):
            motion_surprised()

        elif emo == "all":
            print("[INFO] 모든 감정 실행 (happy → sad → surprised)")
            motion_happy()
            time.sleep(0.5)
            motion_sad()
            time.sleep(0.5)
            motion_surprised()
            print("[INFO] all 완료")

        else:
            print("[ERROR] 감정 선택 오류")
            sys.exit(1)

        print("[INFO] 감정 모션 완료")
        sys.exit(0)

    print("[ERROR] -emo 또는 -set 옵션 필요")
    sys.exit(1)

if __name__ == "__main__":
    main()
