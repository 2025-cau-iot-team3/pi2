# Tiny-RNN

이 프로젝트는 라즈베리파이 기반의 초경량 RNN(진화전략 기반) 로봇 제어 시스템입니다.  
센서 입력(거리, 사물 종류, 자이로, 밝기)을 Tiny RNN이 받아서  
`APPROACH`, `RUN_AWAY`, `TURN_LEFT`, `TURN_RIGHT` 중 하나를 결정하고  
TB6612FNG 모터 드라이버를 통해 실제 이동을 수행합니다.

---

## 📌 프로젝트 파일 구조

```
pi2/
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
 │   ├─ trainer.py
 │   └─ README.md
 └─ logs/
```

---

## 📄 파일 설명

### **1. `rnn/tiny_rnn.py`**
라즈베리파이에서 구동 가능한 초경량 Tiny RNN 모델 구현 파일입니다.
- 입력: 센서 정보(거리, 물체종류, 자이로, 밝기)
- 출력: 행동(action)
- numpy 기반 순전파(forward)만 구현  
- 역전파(backprop) 없음 — 학습은 ES로 수행

---

### **2. `rnn/brain.py`**
Tiny RNN을 감싸는 고수준 인터페이스.
- RNN 초기화  
- 가중치 가져오기 / 설정하기  
- 상태 입력 → 행동 출력(`act()`)

---

### **3. `rnn/brain_es.py`**
유전 알고리즘 기반 **Evolution Strategy (ES)** 구현.
- population 생성
- 각 개체별 노이즈 적용
- 보상 기반 가중치 업데이트
- Tiny RNN 학습 담당

---

### **4. `control/sensors.py`**
로봇의 센서 입력을 소프트웨어적으로 관리.
- 거리 센서 값 (mock)
- 물체 타입 (고양이=무서움 등)
- 자이로 센서 값
- 밝기 센서 값
- 보상 함수(`compute_reward()`)

현재는 시뮬레이션 값을 사용하지만 실제 센서로 쉽게 교체 가능.

---

### **5. `control/move.py`**
TB6612FNG 기반 좌/우 모터 제어.
- `forward()`
- `backward()`
- `left()`
- `right()`
- `stop()`

`motorConfig.json`에 설정된 핀 번호를 읽어서 GPIO 초기화.

---

### **6. `control/motorConfig.json`**
모터 드라이버 핀 매핑을 저장하는 설정 파일입니다.
- LEFT: IN1/IN2/PWM  
- RIGHT: IN1/IN2/PWM  
- STBY: TB6612FNG 스탠바이 핀  

---

### **7. `rnn/trainer.py`**
AI 학습 엔진.
- Tiny RNN + Evolution Strategy 조합
- population 단위 평가
- 세대별 로그 출력
- 로그 파일 자동 저장(`logs/es_train_*.log`)
- `python3 trainer.py 10` → 기본 10세대 학습 수행
- `python3 trainer.py 50` → 50세대 학습 수행

---

### **8. `control/alarmConfig.json`**
알람 기능(시계/알림)을 위한 JSON 저장소.

---

### **9. `control/clock.py`**
현재 시간/날짜 계산 및 알람 로직.
move, brain, trainer와 독립적으로 작동하는 서브 기능.

---

### **10. `logs/`**
ES 학습 로그 자동 저장.

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
