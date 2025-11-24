# trainer.py
import json
import os
import time
import sys
import subprocess
from datetime import datetime
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rnn.brain import Brain
from rnn.brain_es import EvolutionStrategy

# C 데몬이 기록하는 상태 파일(루트, 확장자 없음)
GYRO_STATE = Path(__file__).resolve().parent.parent / "gyro_state"
ULTRA_STATE = Path(__file__).resolve().parent.parent / "ultra_state"
SENSOR_STATE = Path(__file__).resolve().parent.parent / "sensor_state"


# ---------------------------
# 센서 + 모터 유틸
# ---------------------------
MOTOR_BIN = PROJECT_ROOT / "motor" / "move"
_motor_warned = False
_sensor_warned = set()

def _warn_once(key, msg):
    if key in _sensor_warned:
        return
    print(msg)
    _sensor_warned.add(key)

def _clamp_speed(s):
    return max(min(int(s), 100), -100)

def _send_motor(left_speed, right_speed):
    global _motor_warned
    if not MOTOR_BIN.exists() or not os.access(MOTOR_BIN, os.X_OK):
        if not _motor_warned:
            print(f"[WARN] Motor binary not found or not executable: {MOTOR_BIN}")
            _motor_warned = True
        return
    try:
        subprocess.run(
            [str(MOTOR_BIN), "--left", str(_clamp_speed(left_speed)), "--right", str(_clamp_speed(right_speed))],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        if not _motor_warned:
            print(f"[WARN] Failed to send motor command: {e}")
            _motor_warned = True

def stop():
    _send_motor(0, 0)

def _read_state_file(path, max_age=1.0):
    if not path.exists():
        return None
    try:
        with open(path, "r") as f:
            data = json.load(f)
        ts = data.get("ts")
        if ts and time.time() - ts > max_age:
            return None
        return data
    except Exception:
        return None


def read_sensors():
    merged = _read_state_file(SENSOR_STATE, max_age=1.0)
    if merged:
        return merged

    gyro_state = _read_state_file(GYRO_STATE, max_age=1.0)
    ultra_state = _read_state_file(ULTRA_STATE, max_age=1.0)
    if gyro_state or ultra_state:
        data = {
            "dist": 0.0,
            "object": 0,
            "gyro": (0.0, 0.0, 0.0),
            "brightness": 0.0,
            "ts": max(
                (gyro_state or {}).get("ts", 0),
                (ultra_state or {}).get("ts", 0),
            ),
        }
        if ultra_state and "distances" in ultra_state:
            vals = [v for v in ultra_state["distances"].values() if v is not None]
            if vals:
                data["dist"] = min(vals)
        if gyro_state and "gyro" in gyro_state:
            g = gyro_state["gyro"]
            if isinstance(g, (list, tuple)) and len(g) == 3:
                data["gyro"] = tuple(g)
        return data

    data = {
        "dist": 0.0,
        "object": 0,  # 현재 물체 분류 센서 없음 → 기본값
        "gyro": (0.0, 0.0, 0.0),
        "brightness": 0.0,  # 밝기 센서 없음 → 기본값
    }
    try:
        from sensor.ultrasonic import read_all as read_ultrasonic
        distances = read_ultrasonic()
        valid = [d for d in distances.values() if d is not None]
        if valid:
            data["dist"] = min(valid)
    except Exception as e:
        _warn_once("ultrasonic", f"[WARN] Ultrasonic read failed: {e}")
    try:
        from sensor.gyro import read as read_gyro
        _, gyro = read_gyro()
        data["gyro"] = gyro
    except Exception as e:
        _warn_once("gyro", f"[WARN] Gyro read failed: {e}")
    data["ts"] = time.time()
    return data

def compute_reward(sensor_data):
    dist = sensor_data.get("dist") or 0.0
    if dist <= 0:
        return -1.0

    target = 50.0  # 목표 거리(cm) 근처로 유지하도록 보상
    reward = 1.0 - abs(dist - target) / max(target, 1.0)
    return max(-1.0, min(1.0, reward))


# ---------------------------
# 세대 수 인자 처리
# ---------------------------
if len(sys.argv) >= 2:
    try:
        TARGET_GENERATIONS = int(sys.argv[1])
    except:
        TARGET_GENERATIONS = 10
else:
    TARGET_GENERATIONS = 10

print(f"[INFO] Training for {TARGET_GENERATIONS} generations.")


# ---------------------------
# 로그 디렉토리 + 파일명 날짜 포함
# ---------------------------
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
LOG_FILE = LOG_DIR / f"es_train_{timestamp}.log"

def log(message):
    t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{t}] {message}\n")


# ---------------------------
# 모델 초기화
# ---------------------------
brain = Brain()
weights = brain.get_weights()
es = EvolutionStrategy(weights, population=5)

generation = 0


# ---------------------------
# 메인 학습 루프
# ---------------------------
while generation < TARGET_GENERATIONS:

    generation += 1
    print(f"\n========== Generation {generation}/{TARGET_GENERATIONS} ==========\n")
    log(f"----- Generation {generation} -----")

    noises = es.ask()
    rewards = []

    for idx, noise in enumerate(noises):
        print(f"[Gen {generation}] Testing individual {idx+1}/{len(noises)}")

        # 신규 가중치 적용
        new_weights = [w + n * es.sigma for w, n in zip(weights, noise)]
        brain.set_weights(new_weights)

        s = read_sensors()
        left_speed, right_speed = brain.act(s)

        # 행동 실행 (좌/우 속도 직접 전송)
        _send_motor(left_speed, right_speed)

        time.sleep(0.15)

        r = compute_reward(s)
        rewards.append(r)

        # 상세 출력
        print(f"  Sensor: {s}")
        print(f"  Speed : L={left_speed:.1f}, R={right_speed:.1f}")
        print(f"  Reward: {r:.3f}")

        # 로그 저장
        log(f"Gen{generation} | Ind{idx+1} | Sensor={s} | Speed=({left_speed:.1f},{right_speed:.1f}) | Reward={r:.3f}")

    stop()
    time.sleep(0.1)

    weights = es.update(noises, rewards)
    brain.set_weights(weights)

    avg_r = sum(rewards) / len(rewards)
    print(f"\n[Generation {generation}] Average Reward: {avg_r:.3f}")
    log(f"Generation {generation} Average Reward: {avg_r:.3f}")

print("\n🎉 Training complete!")
print(f"Log saved: {LOG_FILE}")
