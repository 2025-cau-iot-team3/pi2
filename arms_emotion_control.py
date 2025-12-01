#!/usr/bin/env python3
import time
import sys

print("=== 팔 서보 감정 모션 시작 ===", flush=True)

# RPi.GPIO import 에러를 눈에 보이게 처리
try:
    import RPi.GPIO as GPIO
except Exception as e:
    print("[ERROR] RPi.GPIO 모듈을 불러오지 못했습니다.", flush=True)
    print("       sudo apt-get install python3-rpi.gpio 를 실행했는지 확인하세요.", flush=True)
    print("       상세 에러:", e, flush=True)
    sys.exit(1)

# -----------------------------
# 핀 설정
# -----------------------------
LEFT_PIN = 17   # 왼팔 서보 신호 (GPIO17, 물리 핀 11)
RIGHT_PIN = 27  # 오른팔 서보 신호 (GPIO27, 물리 핀 13)
PWM_FREQ = 50   # 서보 주파수 50Hz

# 각도 → 듀티비 변환 (대략 0~180도)
def angle_to_duty(angle):
    angle = max(0, min(180, angle))  # 안전하게 클램프
    duty = 2.5 + (angle / 180.0) * 10.0
    print(f"[DEBUG] angle={angle} -> duty={duty:.2f}", flush=True)
    return duty

# -----------------------------
# 서보 초기화 / 종료
# -----------------------------
def setup_servos():
    print("[INFO] GPIO BCM 모드 설정", flush=True)
    GPIO.setmode(GPIO.BCM)
    print(f"[INFO] LEFT_PIN={LEFT_PIN}, RIGHT_PIN={RIGHT_PIN} 출력 설정", flush=True)
    GPIO.setup(LEFT_PIN, GPIO.OUT)
    GPIO.setup(RIGHT_PIN, GPIO.OUT)

    print(f"[INFO] PWM 시작 (freq={PWM_FREQ}Hz)", flush=True)
    left_pwm = GPIO.PWM(LEFT_PIN, PWM_FREQ)
    right_pwm = GPIO.PWM(RIGHT_PIN, PWM_FREQ)

    print("[INFO] 초기 각도 90도로 설정", flush=True)
    left_pwm.start(angle_to_duty(90))
    right_pwm.start(angle_to_duty(90))
    time.sleep(0.5)

    return left_pwm, right_pwm

def cleanup_servos(left_pwm, right_pwm):
    print("[INFO] PWM stop & GPIO cleanup", flush=True)
    left_pwm.stop()
    right_pwm.stop()
    GPIO.cleanup()

# -----------------------------
# 공통 동작: 팔 각도 세팅
# -----------------------------
def set_arms(left_pwm, right_pwm, left_angle, right_angle, delay=0.2):
    print(f"[INFO] set_arms: left={left_angle}, right={right_angle}, delay={delay}", flush=True)
    left_pwm.ChangeDutyCycle(angle_to_duty(left_angle))
    right_pwm.ChangeDutyCycle(angle_to_duty(right_angle))
    time.sleep(delay)

# -----------------------------
# 감정별 모션
# -----------------------------
def motion_happy(left_pwm, right_pwm):
    print("[INFO] 기쁨 모션: 팔 위/아래 2번 흔들기", flush=True)

    down_angle = 60
    up_angle   = 140

    set_arms(left_pwm, right_pwm, down_angle, down_angle, delay=0.4)

    for i in range(2):
        print(f"[INFO] happy wave #{i+1} - UP", flush=True)
        set_arms(left_pwm, right_pwm, up_angle, up_angle, delay=0.25)
        print(f"[INFO] happy wave #{i+1} - DOWN", flush=True)
        set_arms(left_pwm, right_pwm, down_angle, down_angle, delay=0.25)

    print("[INFO] happy 모션 끝, 중간 자세 복귀", flush=True)
    set_arms(left_pwm, right_pwm, 90, 90, delay=0.4)

def motion_sad(left_pwm, right_pwm):
    print("[INFO] 슬픔 모션: 팔 아래로 3초 유지", flush=True)

    down_angle = 40

    set_arms(left_pwm, right_pwm, down_angle, down_angle, delay=0.4)
    print("[INFO] 슬픔 자세 유지 3초", flush=True)
    time.sleep(3.0)

    print("[INFO] sad 모션 끝, 중간 자세 복귀", flush=True)
    set_arms(left_pwm, right_pwm, 90, 90, delay=0.4)

def motion_surprised(left_pwm, right_pwm):
    print("[INFO] 놀람 모션: 팔 위로 3초 유지", flush=True)

    up_angle = 150

    set_arms(left_pwm, right_pwm, up_angle, up_angle, delay=0.4)
    print("[INFO] 놀람 자세 유지 3초", flush=True)
    time.sleep(3.0)

    print("[INFO] surprised 모션 끝, 중간 자세 복귀", flush=True)
    set_arms(left_pwm, right_pwm, 90, 90, delay=0.4)

# -----------------------------
# 메인
# -----------------------------
def main():
    if len(sys.argv) < 2:
        print("사용법: sudo python3 arms_emotion_control.py [happy|sad|surprised]", flush=True)
        return

    emotion = sys.argv[1].lower()
    print(f"[INFO] 선택된 감정: {emotion}", flush=True)

    left_pwm = right_pwm = None

    try:
        left_pwm, right_pwm = setup_servos()

        if emotion == "happy":
            motion_happy(left_pwm, right_pwm)
        elif emotion == "sad":
            motion_sad(left_pwm, right_pwm)
        elif emotion in ("surprised", "surprise"):
            motion_surprised(left_pwm, right_pwm)
        else:
            print("알 수 없는 감정입니다. happy / sad / surprised 중 하나를 사용하세요.", flush=True)
            return

        print("[INFO] 모션 수행 완료. 5초 동안 자세 유지 후 종료 대기.", flush=True)
        time.sleep(5.0)

        print("Ctrl+C 를 눌러 종료하세요.", flush=True)
        while True:
            time.sleep(1.0)

    except KeyboardInterrupt:
        print("\n[INFO] 사용자에 의해 종료 요청 (Ctrl+C)", flush=True)
    except Exception as e:
        print("[ERROR] 예외 발생:", e, flush=True)
    finally:
        if left_pwm is not None and right_pwm is not None:
            cleanup_servos(left_pwm, right_pwm)
        print("[INFO] 프로그램 종료", flush=True)

if __name__ == "__main__":
    main()
