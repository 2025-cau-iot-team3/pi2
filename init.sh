#!/bin/bash

# 절대경로 기준 설정
BASE="/home/iot/pi2"

# --------------------------
# 0) 가상환경 활성화
# --------------------------
source "$BASE/venv/bin/activate"

# --------------------------
# 1) motor/move_daemon 실행
#    - pigpio ON
# --------------------------
cd "$BASE/motor"
"$BASE/motor/move_daemon" &
MOVE_PID=$!

# --------------------------
# 2) sensor/sensor_daemon 실행
#    - pigpio OFF 모드 강제
# --------------------------
cd "$BASE/sensor"
PIGPIO_NO_INIT=1 "$BASE/sensor/sensor_daemon" 20 &
SENSOR_PID=$!

# --------------------------
# 3) 메인 Python 클라이언트 실행
# --------------------------
cd "$BASE"
python3 "$BASE/pi2_client.py"

# --------------------------
# 4) python 종료되면 데몬들 정리
# --------------------------
echo "Stopping daemons..."
kill $MOVE_PID
kill $SENSOR_PID

echo "Done."
