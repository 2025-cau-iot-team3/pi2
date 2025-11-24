import os

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