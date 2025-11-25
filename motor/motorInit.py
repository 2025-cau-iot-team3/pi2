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

def init():
    print("=== motorInit.init() START ===")
    kill_process("move_daemon")
    kill_process("pigpiod")
    run("sudo rm -f /var/run/pigpio.pid")
    run("sudo rm -f /run/pigpio.pid")
    print("[INFO] pigpiod removed (direct mode)")
    daemon_path = os.path.join(os.path.dirname(__file__), "move_daemon")
    if not os.path.isfile(daemon_path):
        print(f"[ERROR] move_daemon not found at {daemon_path}.")
        return False
    print("[INFO] Starting move_daemon...")
    subprocess.Popen(["sudo", daemon_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    time.sleep(1)
    print("\n=== Process Check ===")
    run("ps aux | grep move_daemon")
    print("=== motorInit.init() DONE ===")
    return True

if __name__ == "__main__":
    init()