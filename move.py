# move.py
import RPi.GPIO as GPIO
import time
import json

GPIO.setmode(GPIO.BCM)

# motorConfig.json 불러오기
with open("motorConfig.json", "r") as f:
    cfg = json.load(f)

LEFT_IN1  = cfg["LEFT"]["IN1"]
LEFT_IN2  = cfg["LEFT"]["IN2"]
LEFT_PWM  = cfg["LEFT"]["PWM"]

RIGHT_IN1 = cfg["RIGHT"]["IN1"]
RIGHT_IN2 = cfg["RIGHT"]["IN2"]
RIGHT_PWM = cfg["RIGHT"]["PWM"]

# GPIO 핀 세팅
GPIO.setup(LEFT_IN1, GPIO.OUT)
GPIO.setup(LEFT_IN2, GPIO.OUT)
GPIO.setup(LEFT_PWM, GPIO.OUT)

GPIO.setup(RIGHT_IN1, GPIO.OUT)
GPIO.setup(RIGHT_IN2, GPIO.OUT)
GPIO.setup(RIGHT_PWM, GPIO.OUT)

pwm_left  = GPIO.PWM(LEFT_PWM, 1000)
pwm_right = GPIO.PWM(RIGHT_PWM, 1000)

pwm_left.start(0)
pwm_right.start(0)


def set_left(direction, speed):
    if direction == "F":
        GPIO.output(LEFT_IN1, GPIO.HIGH)
        GPIO.output(LEFT_IN2, GPIO.LOW)
    elif direction == "B":
        GPIO.output(LEFT_IN1, GPIO.LOW)
        GPIO.output(LEFT_IN2, GPIO.HIGH)
    else:
        GPIO.output(LEFT_IN1, GPIO.LOW)
        GPIO.output(LEFT_IN2, GPIO.LOW)

    pwm_left.ChangeDutyCycle(speed)


def set_right(direction, speed):
    if direction == "F":
        GPIO.output(RIGHT_IN1, GPIO.HIGH)
        GPIO.output(RIGHT_IN2, GPIO.LOW)
    elif direction == "B":
        GPIO.output(RIGHT_IN1, GPIO.LOW)
        GPIO.output(RIGHT_IN2, GPIO.HIGH)
    else:
        GPIO.output(RIGHT_IN1, GPIO.LOW)
        GPIO.output(RIGHT_IN2, GPIO.LOW)

    pwm_right.ChangeDutyCycle(speed)


def forward(speed=50):
    set_left("F", speed)
    set_right("F", speed)


def backward(speed=50):
    set_left("B", speed)
    set_right("B", speed)


def left(speed=40):
    # 제자리 회전
    set_left("B", speed)
    set_right("F", speed)


def right(speed=40):
    # 제자리 회전
    set_left("F", speed)
    set_right("B", speed)


def stop():
    set_left("S", 0)
    set_right("S", 0)
