# sensors.py
import random

def read_sensors():
    """임시 랜덤 센서값. 나중에 실제 값으로 교체."""
    dist = random.uniform(5, 150)       # 초음파 거리
    object_id = random.choice([0, 1, 2])  # 0:none,1:cat,2:human
    gyro = (
        random.uniform(-1, 1),
        random.uniform(-1, 1),
        random.uniform(-1, 1),
    )
    brightness = random.uniform(0, 1)

    return {
        "dist": dist,
        "object": object_id,
        "gyro": gyro,
        "brightness": brightness,
    }

def compute_reward(s):
    reward = 0

    if s["object"] == 1:  # cat → 멀어지는게 보상
        reward += s["dist"] / 200.0

    if s["object"] == 2:  # human → 가까워지는게 보상
        reward += (200 - s["dist"]) / 200.0

    if s["dist"] < 10:    # 벽 근접
        reward -= 1.0

    reward += s["brightness"] * 0.05

    return reward
