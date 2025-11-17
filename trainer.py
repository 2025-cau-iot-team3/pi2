# trainer.py
import os
import time
import sys
from datetime import datetime

from brain import Brain
from brain_es import EvolutionStrategy
from sensors import read_sensors, compute_reward
from move import forward, backward, left, right, stop


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

        time.sleep(0.15)

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
