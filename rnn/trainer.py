# trainer.py
import os
import time
import sys
from datetime import datetime
<<<<<<< Updated upstream
=======
from pathlib import Path
import numpy as np
>>>>>>> Stashed changes

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

<<<<<<< Updated upstream
from brain import Brain
from brain_es import EvolutionStrategy
from control.sensors import read_sensors, compute_reward
from control.move import forward, backward, left, right, stop
=======
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
        # 보조 필드 정규화
        distances = []
        dist_map = merged.get("distances") or {}
        if isinstance(dist_map, dict):
            for k in sorted(dist_map.keys()):
                v = dist_map[k]
                distances.append(0.0 if v is None else float(v))
        while len(distances) < 2:
            distances.append(0.0)
        merged["distances"] = distances[:2]
        return merged

    gyro_state = _read_state_file(GYRO_STATE, max_age=1.0)
    ultra_state = _read_state_file(ULTRA_STATE, max_age=1.0)
    if gyro_state or ultra_state:
        data = {
            "dist": 0.0,
            "object": 0,
            "gyro": (0.0, 0.0, 0.0),
            "brightness": 0.0,
            "distances": [0.0, 0.0],
            "ts": max(
                (gyro_state or {}).get("ts", 0),
                (ultra_state or {}).get("ts", 0),
            ),
        }
        if ultra_state and "distances" in ultra_state:
            dist_map = ultra_state["distances"] or {}
            vals = []
            if isinstance(dist_map, dict):
                for k in sorted(dist_map.keys()):
                    v = dist_map[k]
                    vals.append(0.0 if v is None else float(v))
            while len(vals) < 2:
                vals.append(0.0)
            data["distances"] = vals[:2]
            valid = [v for v in vals if v > 0]
            if valid:
                data["dist"] = min(valid)
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
        "distances": [0.0, 0.0],
    }
    try:
        from sensor.ultrasonic import read_all as read_ultrasonic
        distances = read_ultrasonic()
        ordered = []
        for k in sorted(distances.keys()):
            v = distances[k]
            ordered.append(0.0 if v is None else float(v))
        while len(ordered) < 2:
            ordered.append(0.0)
        data["distances"] = ordered[:2]
        valid = [d for d in ordered if d > 0]
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
>>>>>>> Stashed changes


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
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
LOG_FILE = f"{LOG_DIR}/es_train_{timestamp}.log"

MODELS_DIR = PROJECT_ROOT / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

def log(message):
    t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{t}] {message}\n")


# ---------------------------
# 학습(study) & 추론(infer) 헬퍼
# ---------------------------
def study(target_generations=10, population=5):
    """ES 기반 학습을 수행하고 각 세대 가중치를 models 디렉터리에 저장."""
    brain = Brain()
    weights = brain.get_weights()
    es = EvolutionStrategy(weights, population=population)

    generation = 0

    while generation < target_generations:
        generation += 1
        print(f"\n========== Generation {generation}/{target_generations} ==========\n")
        log(f"----- Generation {generation} -----")

        noises = es.ask()
        rewards = []

        for idx, noise in enumerate(noises):
            print(f"[Gen {generation}] Testing individual {idx+1}/{len(noises)}")

            # 신규 가중치 적용
            new_weights = [w + n * es.sigma for w, n in zip(weights, noise)]
            brain.set_weights(new_weights)

            s = read_sensors()
            left_speed, right_speed, emotion = brain.act(s)

            # 행동 실행 (좌/우 속도 직접 전송)
            _send_motor(left_speed, right_speed)

            time.sleep(0.15)

            r = compute_reward(s)
            rewards.append(r)

            # 상세 출력
            print(f"  Sensor: {s}")
            print(f"  Speed : L={left_speed:.1f}, R={right_speed:.1f}")
            if emotion is not None:
                print(f"  Emotion: {emotion}")
            print(f"  Reward: {r:.3f}")

            # 로그 저장
            log(f"Gen{generation} | Ind{idx+1} | Sensor={s} | Speed=({left_speed:.1f},{right_speed:.1f}) | Emotion={emotion} | Reward={r:.3f}")

        stop()
        time.sleep(0.1)

        weights = es.update(noises, rewards)
        brain.set_weights(weights)

        avg_r = sum(rewards) / len(rewards)
        print(f"\n[Generation {generation}] Average Reward: {avg_r:.3f}")
        log(f"Generation {generation} Average Reward: {avg_r:.3f}")

        model_path = save_weights(weights, generation)
        log(f"[MODEL] Saved generation {generation} to {model_path.name}")
        print(f"[MODEL] Saved: {model_path}")

    print("\n🎉 Training complete!")
    print(f"Log saved: {LOG_FILE}")
    return weights


_infer_brain = None
_infer_weights = None

def load_inference(weights):
    """베스트 가중치로 경량 추론용 Brain 준비."""
    global _infer_brain, _infer_weights
    if _infer_brain is None:
        _infer_brain = Brain()
    _infer_weights = weights
    _infer_brain.set_weights(weights)

def infer(sensor_data):
    """학습된 베스트 가중치로 실시간 판단."""
    if _infer_brain is None or _infer_weights is None:
        raise RuntimeError("Inference brain not loaded. Call load_inference(weights) first.")
    return _infer_brain.act(sensor_data)


def save_weights(weights, generation):
    """모델 가중치를 models/model_gen_XXXX.npz로 저장."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    filename = MODELS_DIR / f"model_gen_{generation:04d}.npz"
    np.savez(filename, *weights)
    return filename

<<<<<<< Updated upstream
        s = read_sensors()
        action = brain.act(s)

        # 행동 실행
        if action == "RUN_AWAY":
            backward(speed=60)
        elif action == "APPROACH":
            forward(speed=50)
        elif action == "TURN_LEFT":
            left(speed=40)
        elif action == "TURN_RIGHT":
            right(speed=40)
=======

def load_weights_from_file(path):
    """저장된 npz에서 가중치 리스트를 복원."""
    with np.load(path, allow_pickle=False) as data:
        arrays = [data[key] for key in data.files]
    return arrays
>>>>>>> Stashed changes


<<<<<<< Updated upstream
        r = compute_reward(s)
        rewards.append(r)

        # 상세 출력
        print(f"  Sensor: {s}")
        print(f"  Action: {action}")
        print(f"  Reward: {r:.3f}")

        # 로그 저장
        log(f"Gen{generation} | Ind{idx+1} | Sensor={s} | Action={action} | Reward={r:.3f}")

    stop()
    time.sleep(0.1)

    weights = es.update(noises, rewards)
    brain.set_weights(weights)

    avg_r = sum(rewards) / len(rewards)
    print(f"\n[Generation {generation}] Average Reward: {avg_r:.3f}")
    log(f"Generation {generation} Average Reward: {avg_r:.3f}")

print("\n🎉 Training complete!")
print(f"Log saved: {LOG_FILE}")
=======
if __name__ == "__main__":
    latest_weights = study(TARGET_GENERATIONS, population=5)
    load_inference(latest_weights)
    print("[INFO] Training finished. Latest weights loaded for inference.")
>>>>>>> Stashed changes
