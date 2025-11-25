# pi2 로봇 컨트롤 시스템

라즈베리파이에서 자이로/초음파 센서를 읽어 공유 파일에 기록하고, 간단한 규칙 기반 브레인이 모터 속도를 결정합니다. 웹소켓 클라이언트(`pi2_client.py`)로 다른 Pi 서버와 통신해 YOLO 라벨을 받고, 로컬 모터 드라이버에 명령을 전달합니다.

## 전체 흐름
- `sensor/sensor_daemon`이 `cfg/sensorConfig.json`을 읽어 MPU6050 + 초음파 값을 주기적으로 측정하고 `sensor/sensor_state`(JSON)에 기록.
- YOLO 라벨을 줄 단위로 `sensor/yolo_obj`에 쓰면 브레인이 감정/동작을 결정.
- `sensor/brain.py`의 `BrainRunner`가 `sensor_state`/`yolo_obj`를 읽어 감정/모터 명령을 계산.
- `motor/move_daemon`이 `motor/motor_cmd`를 감시해 TB6612FNG를 구동하고, `motor/move.py`가 파일에 좌우 속도를 기록.
- `pi2_client.py`는 외부 서버(기본 `ws://192.168.0.22:8000`)와 연결해 브레인 루프를 띄우고, 원격 명령/YOLO 결과를 주고받습니다.

## 디렉터리 개요
- `sensor/`  
  - `sensor_daemon.c` / `sensor_state` / `yolo_obj` : 센서 데몬 소스와 출력 파일  
  - `sensor.py` : `sensor_state` 파서  
  - `brain.py` : 규칙 기반 브레인 + `BrainRunner` 비동기 루프
- `motor/`  
  - `move_daemon.c` / `move_daemon` : `motor_cmd` 감시 → TB6612FNG 제어  
  - `move.py` : `motor_cmd`에 좌우 속도(-100~100) 기록 유틸  
  - `motorInit.py` : 기존 데몬/`pigpiod` 정리 후 `move_daemon`를 sudo로 구동
- `cfg/` : `sensorConfig.json`(MPU6050/초음파 핀, 자이로 neutral), `objectConfig.json`(선호/비선호 라벨), `motorConfig.json`, `alarmConfig.json`
- `util/clock.py` : 시간/날짜/알람/날씨 CLI
- `pi2_client.py` : 웹소켓 하드웨어 클라이언트(브레인 루프와 연동)

## 사전 설정
1. `cfg/sensorConfig.json`에서 MPU6050 I2C 버스/주소, 초음파 `trigger_pin`/`echo_pin`, `neutral` 오프셋을 하드웨어에 맞게 수정.
2. `cfg/motorConfig.json`(또는 동일 내용을 `motor/motorConfig.json`에 반영)에서 TB6612FNG 핀 매핑 확인.
3. `cfg/objectConfig.json`에 좋아하는 라벨(`like`) / 피하고 싶은 라벨(`dislike`)을 입력.
4. 웹소켓 서버 IP가 다르면 `pi2_client.py`의 `PI_1_IP`를 수정.

## 빌드 및 실행
1) 센서 데몬 빌드/실행 (`sensor/` 디렉터리)  
```bash
cd sensor
gcc sensor_daemon.c -o sensor_daemon -ljson-c -lpigpio -lrt -pthread
sudo ./sensor_daemon       # 기본 20 Hz, sensor_state 생성
# sudo ./sensor_daemon 10   # 주기를 10 Hz로 조정할 때
```

2) 모터 데몬 실행 (`motor/` 디렉터리)  
```bash
cd motor
gcc move_daemon.c -o move_daemon -ljson-c -lpigpio -lrt -pthread   # 필요 시 빌드
python3 motorInit.py       # 기존 프로세스/피지피아이오 정리 후 sudo로 데몬 실행
python3 -c "from move import set_motor; set_motor(30, 30)"  # 수동 테스트
```

3) 브레인 루프 단독 테스트  
```bash
python3 - <<'PY'
from sensor.brain import BrainRunner
import asyncio
asyncio.run(BrainRunner.get().loop(0.5))
PY
# sensor_state, yolo_obj 값을 변경하면 터미널에 (left, right, emotion) 로그가 찍힙니다.
```

4) 웹소켓 클라이언트(Pi 서버 연동)  
```bash
python3 pi2_client.py
```

## 파일 포맷 참고
- `sensor/sensor_state` 예시  
  ```json
  {"ultrasonic_1": 120.0, "ultrasonic_2": 150.0, "gyro": [0.1, -0.2, 0.0], "ts": 1763970671}
  ```
- `sensor/yolo_obj` : 각 줄에 감지된 라벨(신뢰도 높은 순). 비어 있으면 브레인은 객체 없이 동작.
