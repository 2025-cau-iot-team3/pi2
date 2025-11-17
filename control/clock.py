import json
import os
import sys
from datetime import datetime
from pathlib import Path
import requests

BASE_DIR = Path(__file__).resolve().parent
ALARM_FILE = BASE_DIR / "alarmConfig.json"

def get_weather_no_api(city="Seoul"):
    url = f"https://wttr.in/{city}?format=j1"

    try:
        res = requests.get(url, timeout=5)
        data = res.json()

        # 현재 기온
        temp = data["current_condition"][0]["temp_C"]
        # 설명
        desc = data["current_condition"][0]["weatherDesc"][0]["value"]
        # 습도
        humidity = data["current_condition"][0]["humidity"]

        return f"{city} {temp}°C, {desc}, 습도 {humidity}%"

    except Exception as e:
        return f"Weather error: {e}"

def current_time_hm():
    return datetime.now().strftime("%H:%M")

def current_date_md():
    return datetime.now().strftime("%m/%d")

# ----------------------------
# Alarm JSON 관리
# ----------------------------

def load_alarms():
    if not os.path.exists(ALARM_FILE):
        return []
    with open(ALARM_FILE, "r") as f:
        return json.load(f)

def save_alarms(alarms):
    with open(ALARM_FILE, "w") as f:
        json.dump(alarms, f, indent=4)

# ----------------------------
# Alarm 기능
# ----------------------------

def add_alarm(time_str, label=""):
    alarms = load_alarms()
    alarms.append({"time": time_str, "label": label})
    save_alarms(alarms)
    print(f"Alarm added: {time_str} {label}")

def remove_alarm(time_str):
    alarms = load_alarms()
    updated = [a for a in alarms if a["time"] != time_str]

    if len(updated) == len(alarms):
        print("No alarm found with that time.")
        return

    save_alarms(updated)
    print(f"Alarm removed: {time_str}")

def list_alarms():
    alarms = load_alarms()
    if not alarms:
        print("No alarms set.")
        return

    print("Current Alarms:")
    for a in alarms:
        print(f"- {a['time']}  {a['label']}")

# ----------------------------
# Command Line Entry
# ----------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python dtManager.py time")
        print("  python dtManager.py date")
        print("  python dtManager.py add HH:MM [label]")
        print("  python dtManager.py remove HH:MM")
        print("  python dtManager.py list")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "time":
        print(current_time_hm())

    elif cmd == "date":
        print(current_date_md())

    elif cmd == "add":
        if len(sys.argv) < 3:
            print("Usage: python dtManager.py add HH:MM [label]")
            sys.exit(1)
        time_str = sys.argv[2]
        label = sys.argv[3] if len(sys.argv) >= 4 else ""
        add_alarm(time_str, label)

    elif cmd == "remove":
        if len(sys.argv) < 3:
            print("Usage: python dtManager.py remove HH:MM")
            sys.exit(1)
        remove_alarm(sys.argv[2])

    elif cmd == "list":
        list_alarms()
    elif cmd == "weather":
        city = sys.argv[2] if len(sys.argv) >= 3 else "Seoul"
        print(get_weather_no_api(city))
    else:
        print("Unknown command.")
