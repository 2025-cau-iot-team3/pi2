# Tiny-RNN

이 프로젝트는 라즈베리파이 기반의 초경량 RNN(진화전략 기반) 로봇 제어 시스템입니다.  
센서 입력(거리, 사물 종류, 자이로, 밝기)을 Tiny RNN이 받아서  
좌/우 트랙 속도(각각 -100~100)를 직접 결정하고  
TB6612FNG 모터 드라이버를 통해 실제 이동을 수행합니다.

---

## 📌 프로젝트 파일 구조

```
pi2/
 ├─ logs/
 ├─ motor/
 │   ├─ move              # 좌/우 속도 명령을 motor_cmd에 기록하는 바이너리
 │   ├─ move_daemon       # pigpio 기반 모터 제어 데몬
 │   ├─ motorInit.py      # 데몬/서비스 초기화 스크립트
 │   ├─ move.c
 │   └─ move_daemon.c
 ├─ sensor/
 │   ├─ gyro.c            # MPU6050를 C로 읽어 gyro_state에 기록
 │   ├─ ultrasonic.c      # 초음파를 C로 읽어 ultra_state에 기록
 │   ├─ sensor_daemon.c   # 자이로+초음파를 통합 폴링해 sensor_state에 기록
 │   ├─ ultrasonic.py     # 초음파 센서 읽기
 │   ├─ gyro.py           # MPU6050 자이로/가속도
 │   ├─ sensor_daemon.py  # 센서 값 캐싱 데몬
 │   └─ test.py           # 간단한 센서 테스트
 ├─ util/
 │   └─ clock.py
 ├─ cfg/
 │   ├─ objectConfig.json  # object 문자열을 like/dislike로 구분
 │   ├─ motorConfig.json   # TB6612FNG 핀 매핑
 │   ├─ sensorConfig.json  # 초음파 핀/주소 설정
 │   └─ alarmConfig.json   # 알람 설정
 └─ rnn/
     ├─ brain.py
     ├─ brain_es.py
     ├─ tiny_rnn.py
     └─ trainer.py
```

---

## 📄 파일 설명

### 1. `rnn/tiny_rnn.py`
라즈베리파이에서 구동 가능한 초경량 Tiny RNN 모델 구현 파일입니다.
- 입력: 센서 정보(거리, 물체종류, 자이로, 밝기)
- 출력: 좌/우 트랙 속도(-100~100)
- numpy 기반 순전파(forward)만 구현  
- 역전파(backprop) 없음 — 학습은 ES로 수행

#### 사용법
```python
from rnn.tiny_rnn import TinyRNN
rnn = TinyRNN(input_size=6, hidden_size=8, output_size=2)
output = rnn.step([0.1, 0, 0.0, 0.0, 0.0, 0.5])
print(output)  # 좌/우 속도 원시 출력
```

---

### 2. `rnn/brain.py`
Tiny RNN을 감싸는 고수준 인터페이스.
- RNN 초기화  
- 가중치 가져오기 / 설정하기  
- 상태 입력 → 행동 출력(`act()`)
- `cfg/objectConfig.json`의 like/dislike 리스트를 사용해 object 문자열을 스칼라(1 / -1 / 0)로 인코딩

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

### 3. `rnn/brain_es.py`
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

### 4. `rnn/trainer.py`
Tiny RNN + ES 학습 엔진.
- population 단위 평가, 세대별 로그 출력
- 로그 파일 자동 저장(`logs/es_train_*.log`)
- `sensor/ultrasonic.py`, `sensor/gyro.py`를 통해 센서 값을 읽고  
  `motor/move` 바이너리를 호출해 좌/우 속도 명령을 전송

#### 사용법
```bash
# 기본 10세대 학습
python3 rnn/trainer.py

# 50세대 학습
python3 rnn/trainer.py 50
```

---

### 5. `sensor/ultrasonic.py`
초음파 센서를 읽어 거리를 반환.
- `cfg/sensorConfig.json`에서 type이 `distance`인 센서를 자동 탐색
- `read(name)`, `read_all()` 제공
 - `sensor_daemon.c`가 실행 중이면 캐시된 값을 활용해 입출력 부하를 줄일 수 있음

#### 사용법
```python
from sensor.ultrasonic import read_all
print(read_all())
```

---

### 6. `sensor/gyro.py`
MPU6050 가속도/자이로를 읽어 튜플 `(acc, gyro)` 반환.

#### 사용법
```python
from sensor.gyro import read
acc, gyro = read()
print(acc, gyro)
```

---

### 7. `sensor/gyro.c` & `sensor/ultrasonic.c`
센서 값을 C로 직접 폴링해 프로젝트 루트의 확장자 없는 state 파일에 기록.
- gyro → `./gyro_state`
- ultra → `./ultra_state`
- `rnn/trainer.py`는 해당 state가 있으면 하드웨어 I/O 없이 즉시 사용

#### 빌드/사용 예시
```bash
# gyro (기본 50Hz)
gcc sensor/gyro.c -o sensor/gyro -ljson-c
sudo ./sensor/gyro 100   # 100Hz 폴링

# ultrasonic (기본 20Hz)
gcc sensor/ultrasonic.c -o sensor/ultrasonic -ljson-c -lpigpio -lrt -pthread
sudo ./sensor/ultrasonic 40   # 40Hz 폴링
```

---

### 8. `cfg/sensorConfig.json`
센서 핀/주소 설정.
- 초음파 센서 trigger/echo BCM 핀과 timeout 설정  
- mpu6050 버스/주소 설정

---

### 9. `motor/` (`move`, `move_daemon`, `motorInit.py`)
- `move`: `--left/-l`, `--right/-r` 옵션으로 좌우 속도를 설정하면 `motor_cmd`에 기록하는 바이너리
- `move_daemon`: `motor_cmd`를 감시하며 pigpio로 실제 모터 제어
- `motorInit.py`: 이전 프로세스 종료 후 `move_daemon`을 기동하는 스크립트
- `cfg/motorConfig.json`: TB6612FNG 핀 매핑 저장

#### 사용법
```bash
cd motor
python3 motorInit.py  # sudo 필요
./move --left 60 --right 60
```

---

### 10. `util/clock.py` (`cfg/alarmConfig.json`)
현재 시간/날짜 계산 및 알람 로직.
- 알람 추가/삭제/목록 관리 시 `cfg/alarmConfig.json`을 업데이트

#### 사용법
```bash
python3 util/clock.py time
python3 util/clock.py add 08:00 모닝콜
python3 util/clock.py list
```

---

### 11. `sensor/sensor_daemon.c`
자이로+초음파를 C로 통합 폴링해 루트 `sensor_state`에 기록하는 데몬.
- `rnn/trainer.py`가 최우선으로 읽는 상태 파일

#### 빌드/사용 예시
```bash
gcc sensor/sensor_daemon.c -o sensor/sensor_daemon -ljson-c -lpigpio -lrt -pthread -li2c
sudo ./sensor/sensor_daemon 40   # 40Hz 폴링, 기본 20Hz
```

> 참고: 파이썬 버전(`sensor_daemon.py`)은 빠른 테스트용으로 남겨둠.

#### 파이썬 테스트용
```bash
# 20Hz 폴링(기본)
python3 sensor/sensor_daemon.py

# 50Hz 폴링
python3 sensor/sensor_daemon.py --hz 50
```

---

### 12. `logs/`
ES 학습 로그 자동 저장.
- `rnn/trainer.py` 실행 시 `logs/es_train_YYYY-MM-DD_HH-MM-SS.log` 생성
- 최신 학습 기록 확인: `tail -f logs/es_train_*.log`

---

## 🚀 사용 예시

- 기본 학습: `python3 rnn/trainer.py`  
- 50세대 학습: `python3 rnn/trainer.py 50`  
- 모터 데몬 구동: `cd motor && python3 motorInit.py` 실행 후 `./move --left 50 --right 50`  
- 센서 테스트: `python3 sensor/test.py`

---
