# Tiny-RNN

이 프로젝트는 라즈베리파이 기반의 초경량 RNN(진화전략 기반) 로봇 제어 시스템입니다.  
센서 입력(거리, 사물 종류, 자이로, 밝기)을 Tiny RNN이 받아서  
`APPROACH`, `RUN_AWAY`, `TURN_LEFT`, `TURN_RIGHT` 중 하나를 결정하고  
TB6612FNG 모터 드라이버를 통해 실제 이동을 수행합니다.

---

## 📌 프로젝트 파일 구조

```
pi2/
 ├─ logs/*
 ├─ control/
 │   ├─ alarmConfig.json
 │   ├─ clock.py
 │   ├─ motorConfig.json
 │   ├─ move.py
 │   └─ sensors.py
 ├─ rnn/
 │   ├─ brain.py
 │   ├─ brain_es.py
 │   ├─ tiny_rnn.py
 │   └─ trainer.py
 └─ README.md
```

---

## 📄 파일 설명

### **1. `rnn/tiny_rnn.py`**
라즈베리파이에서 구동 가능한 초경량 Tiny RNN 모델 구현 파일입니다.
- 입력: 센서 정보(거리, 물체종류, 자이로, 밝기)
- 출력: 행동(action)
- numpy 기반 순전파(forward)만 구현  
- 역전파(backprop) 없음 — 학습은 ES로 수행

#### 사용법
```python
from rnn.tiny_rnn import TinyRNN
rnn = TinyRNN(input_size=6, hidden_size=8, output_size=4)
output = rnn.step([0.1, 0, 0.0, 0.0, 0.0, 0.5])
print(output.argmax())
```

---

### **2. `rnn/brain.py`**
Tiny RNN을 감싸는 고수준 인터페이스.
- RNN 초기화  
- 가중치 가져오기 / 설정하기  
- 상태 입력 → 행동 출력(`act()`)

#### 사용법
```python
from rnn.brain import Brain
brain = Brain()
action = brain.act({
    "dist": 50,
    "object": 1,
    "gyro": (0.0, 0.0, 0.0),
    "brightness": 0.4
})
print(action)
```

---

### **3. `rnn/brain_es.py`**
유전 알고리즘 기반 **Evolution Strategy (ES)** 구현.
- population 생성
- 각 개체별 노이즈 적용
- 보상 기반 가중치 업데이트
- Tiny RNN 학습 담당

#### 사용법
```python
from rnn.brain_es import EvolutionStrategy
weights = [...]  # TinyRNN.get_weights() 결과
es = EvolutionStrategy(weights, sigma=0.1, lr=0.03, population=5)
noises = es.ask()
# 보상 계산 후
updated = es.update(noises, rewards=[0.1]*len(noises))
```

---

### **4. `control/sensors.py`**
로봇의 센서 입력을 소프트웨어적으로 관리.
- 거리 센서 값 (mock)
- 물체 타입 (고양이=무서움 등)
- 자이로 센서 값
- 밝기 센서 값
- 보상 함수(`compute_reward()`)

현재는 시뮬레이션 값을 사용하지만 실제 센서로 쉽게 교체 가능.

#### 사용법
```python
from control.sensors import read_sensors, compute_reward
state = read_sensors()
reward = compute_reward(state)
print(state, reward)
```

---

### **5. `control/move.py`**
TB6612FNG 기반 좌/우 모터 제어.
- `forward()`
- `backward()`
- `left()`
- `right()`
- `stop()`

`motorConfig.json`에 설정된 핀 번호를 읽어서 GPIO 초기화.

#### 사용법
라즈베리파이에서 GPIO가 초기화된 후 아래와 같이 단독 테스트를 수행합니다.
```bash
python3 - <<'PY'
from control.move import forward, stop
forward(60)
import time; time.sleep(1.0)
stop()
PY
```

---

### **6. `control/motorConfig.json`**
모터 드라이버 핀 매핑을 저장하는 설정 파일입니다.
- LEFT: IN1/IN2/PWM  
- RIGHT: IN1/IN2/PWM  
- STBY: TB6612FNG 스탠바이 핀  

#### 사용법
1. TB6612FNG와 연결된 BCM 핀 번호를 확인합니다.  
2. `control/motorConfig.json`의 값을 해당 핀 번호로 수정합니다.  
3. 저장 후 `control/move.py`를 재실행하면 새로운 설정이 반영됩니다.

---

### **7. `rnn/trainer.py`**
AI 학습 엔진.
- Tiny RNN + Evolution Strategy 조합
- population 단위 평가
- 세대별 로그 출력
- 로그 파일 자동 저장(`logs/es_train_*.log`)

#### 사용법
```bash
# 기본 10세대 학습
python3 rnn/trainer.py

# 50세대 학습
python3 rnn/trainer.py 50
```

---

### **8. `control/alarmConfig.json`**
알람 기능(시계/알림)을 위한 JSON 저장소.

#### 사용법
`control/clock.py`로 알람을 추가/삭제하면 자동으로 수정됩니다.  
직접 수정하려면 JSON 배열에 `{"time": "HH:MM", "label": "메모"}` 형태로 추가하십시오.

---

### **9. `control/clock.py`**
현재 시간/날짜 계산 및 알람 로직.
move, brain, trainer와 독립적으로 작동하는 서브 기능.

#### 사용법
```bash
# 현재 시각
python3 control/clock.py time

# 알람 추가
python3 control/clock.py add 08:00 모닝콜

# 알람 목록
python3 control/clock.py list
```

---

### **10. `logs/`**
ES 학습 로그 자동 저장.

#### 사용법
- `rnn/trainer.py` 실행 시 `logs/es_train_YYYY-MM-DD_HH-MM-SS.log`가 생성됩니다.  
- 최신 학습 기록을 확인하려면 `tail -f logs/es_train_*.log` 명령을 사용하십시오.

---

## 🚀 사용 예시

### **기본 학습 (10세대)**

```
python3 rnn/trainer.py
```

### **50세대 학습**

```
python3 rnn/trainer.py 50
```

### **모터 단독 테스트**

```
python3 control/move.py
```

---

## 🧠 전체 작동 흐름

```
센서 읽기 → Tiny RNN → 행동 결정 → 모터 제어 → 보상 계산 → ES 업데이트
```

---

## ✔ 확장 가능 기능

- 실제 초음파/자이로 센서 연결
- 카메라 기반 물체 인식 결합
- 더 깊은 RNN(GRU-lite) 사용
- 경량 CNN + Tiny RNN 결합
- 보상 설계 고도화
- 행동 로그 기반 행동 그래프 자동 생성
