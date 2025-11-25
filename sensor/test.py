import time
import json

FILE_PATH = "sensor_state"

while True:
    try:
        with open(FILE_PATH, "r") as f:
            data = f.read().strip()
            print(data)
    except Exception as e:
        print(f"Error reading {FILE_PATH}: {e}")

    time.sleep(1)
