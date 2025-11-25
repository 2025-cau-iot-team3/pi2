#!/bin/bash

# --------------------------
# 0) 가상환경 활성화
# --------------------------
source venv/bin/activate

# --------------------------
# 1) motor/move_daemon 실행
#    - pigpio ON
# --------------------------
cd motor
sudo ./move_daemon &
MOVE_PID=$!

# --------------------------
# 2) sensor/sensor_daemon 실행
#    - pigpio OFF 모드 강제
#      (pigpio 충돌 방지)
# --------------------------
cd ../sensor
sudo PIGPIO_NO_INIT=1 ./sensor_daemon 20 &
SENSOR_PID=$!

# --------------------------
# 3) 메인 Python 클라이언트 실행
# --------------------------
cd ../
python3 pi2_client.py

# --------------------------
# 4) python 종료되면 데몬들 정리
# --------------------------
echo "Stopping daemons..."
sudo kill $MOVE_PID
sudo kill $SENSOR_PID

echo "Done."
