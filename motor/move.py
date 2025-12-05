import os
import argparse

CMD_PATH = os.path.join(os.path.dirname(__file__), "motor_cmd")

def clamp(value):
    return max(-100, min(100, int(value)))

def set_motor(left, right):
    left = clamp(left)
    right = clamp(right)

    try:
        with open(CMD_PATH, "w") as f:
            f.write(f"{left} {right}\n")
    except Exception as e:
        print("[move.py] ERROR:", e)


# ---------------------------------------------------------
# __main__ 엔트리포인트 추가
# ---------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-set", "--set_speed", nargs=2, type=int,
                        metavar=("LEFT", "RIGHT"),
                        help="왼/오 모터 속도 설정 (-100 ~ 100)")

    args = parser.parse_args()

    if args.set_speed:
        L = args.set_speed[0]
        R = args.set_speed[1]
        print(f"[CMD] set_motor({L}, {R})")
        set_motor(L, R)
