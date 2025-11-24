# pi2 로봇 컨트롤 시스템

라즈베리파이 기반 주행 로봇. 센서 상태를 주기적으로 수집해 파일로 공유하고, 모터 데몬이 명령을 실행합니다. 브레인은 RNN 없이 규칙/선호도(`cfg/objectConfig.json`) 기반으로 감정과 속도를 결정합니다.

## 디렉터리 개요
- `sensor/`  
  - `sensor_daemon.c` : 자이로+초음파를 읽어 루트 `sensor_state`(flat JSON)에 기록  
  - `gyro.c`, `ultrasonic.c` : 단일 센서 폴링 바이너리  
  - `sensor_daemon.py` : 간단 파이썬 캐시 데몬(테스트용)
- `motor/`  
  - `move` : 좌우 속도를 `motor_cmd`에 기록하는 CLI  
  - `move_daemon` : `motor_cmd` 감시 → TB6612FNG 제어  
  - `motorInit.py` : 데몬 실행 스크립트
- `brain/`  
  - `brain.py` : 선호도/규칙 기반 브레인 (neutral이면 모터 0)  
  - `test.py` : `--object --gyro GX GY GZ --distance D1 D2`로 브레인 출력 확인
- `cfg/` : `objectConfig.json`(선호도 ±100), `sensorConfig.json`(MPU6050/초음파/neutral), `motorConfig.json`, `alarmConfig.json`
- 기타 : `util/clock.py`(알람/시간), `logs/`, `models_cl/`(필요 시 생성)

## 필수 설정
1. `cfg/sensorConfig.json` : MPU6050 버스/주소, 초음파 트리거/에코 핀, `neutral` 자이로 오프셋 확인
2. `cfg/motorConfig.json` : TB6612FNG 핀 매핑 확인
3. `cfg/objectConfig.json` : object 선호도(±100) 입력

## 실행 순서
1) 센서 데몬 빌드/실행  
   ```bash
   gcc sensor/sensor_daemon.c -o sensor/sensor_daemon -ljson-c -lpigpio -lrt -pthread -li2c
   sudo ./sensor/sensor_daemon   # sensor_state 생성
   ```
2) 모터 데몬 실행  
   ```bash
   cd motor
   python3 motorInit.py  # sudo 필요
   ./move --left 50 --right 50
   ```
3) 브레인 테스트  
   ```bash
   python brain/test.py --object dog --gyro 0.1 0.2 0.0 --distance 120 150
   ```

## 동작 요약
- 센서 상태는 루트 `sensor_state`(flat JSON)로 공유됩니다.
- 브레인은 규칙(자이로/거리/선호도)으로 감정 결정 → neutral이면 정지, 나머지는 선호도/거리 비례 속도로 전후진.
- 모터 데몬은 `motor_cmd` 파일을 지속 감시하여 명령을 반영합니다.
