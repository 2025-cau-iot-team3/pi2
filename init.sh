#!/bin/bash
set -e

BASE="$(cd "$(dirname "$0")" && pwd)"

echo "============================================="
echo "  PI2 INIT SCRIPT START"
echo "  BASE = $BASE"
echo "============================================="

# --------------------------
# 1) Python venv 활성화
# --------------------------
if [ -f "$BASE/venv/bin/activate" ]; then
    echo "[INFO] Activating venv..."
    source "$BASE/venv/bin/activate"
else
    echo "[ERROR] venv not found at $BASE/venv"
    exit 1
fi

# --------------------------
# 2) motorInit.py 실행
# --------------------------
echo "[INFO] Running motorInit.py ..."
python3 "$BASE/motor/motorInit.py"

sleep 1

# --------------------------
# 3) pi2_client.py 실행
# --------------------------
echo "[INFO] Starting pi2_client.py ..."
python3 "$BASE/pi2_client.py"

# --------------------------
# 4) 종료 처리
# --------------------------
echo "[INFO] pi2_client.py exited. Cleaning up..."
# motorInit.py already kills old daemons, so no explicit kill needed here.

echo "============================================="
echo "  INIT DONE"
echo "============================================="
