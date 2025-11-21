#!/usr/bin/env python3
import os
import subprocess
import time
import signal

def run(cmd):
    print(f"[CMD] {cmd}")
    subprocess.run(cmd, shell=True)

def kill_process(name):
    print(f"[KILL] Searching for '{name}'...")
    try:
        output = subprocess.check_output(f"pgrep -f {name}", shell=True).decode().strip()
        pids = [p for p in output.split("\n") if p.isdigit()]

        for pid in pids:
            print(f"[KILL] Trying to kill PID={pid}")
            try:
                os.kill(int(pid), signal.SIGKILL)
                print(f"[KILL] PID={pid} killed")
            except ProcessLookupError:
                print(f"[WARN] PID={pid} already dead, skipping")
            except Exception as e:
                print(f"[ERROR] Failed to kill PID={pid}: {e}")

    except subprocess.CalledProcessError:
        print(f"[INFO] No '{name}' process found.")


print("=== motorInit.py START ===")

# 1) 기존 move_daemon 종료
kill_process("move_daemon")

# 2) 기존 pigpiod 종료
kill_process("pigpiod")

# 3) PID 파일 제거
run("sudo rm -f /var/run/pigpio.pid")
run("sudo rm -f /run/pigpio.pid")

print("[INFO] pigpiod removed (direct mode)")

# 4) move_daemon 실행
if not os.path.isfile("./move_daemon"):
    print("[ERROR] move_daemon not found in current directory.")
    exit(1)

print("[INFO] Starting move_daemon...")
p = subprocess.Popen(["sudo", "./move_daemon"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

time.sleep(1)

print("\n=== Process Check ===")
run("ps aux | grep move_daemon")

print("=== motorInit.py DONE ===")
