import json
import RPi.GPIO as GPIO
import time

class Motor:
    def __init__(self, in1, in2, pwm_pin, pwm_freq=1000):
        self.in1 = in1
        self.in2 = in2
        self.pwm_pin = pwm_pin
        GPIO.setup(self.in1, GPIO.OUT)
        GPIO.setup(self.in2, GPIO.OUT)
        GPIO.setup(self.pwm_pin, GPIO.OUT)
        self.pwm = GPIO.PWM(self.pwm_pin, pwm_freq)
        self.pwm.start(0)

    def forward(self, speed):
        GPIO.output(self.in1, GPIO.HIGH)
        GPIO.output(self.in2, GPIO.LOW)
        self.pwm.ChangeDutyCycle(speed)

    def backward(self, speed):
        GPIO.output(self.in1, GPIO.LOW)
        GPIO.output(self.in2, GPIO.HIGH)
        self.pwm.ChangeDutyCycle(speed)

    def stop(self):
        self.pwm.ChangeDutyCycle(0)
        GPIO.output(self.in1, GPIO.LOW)
        GPIO.output(self.in2, GPIO.LOW)

    def cleanup(self):
        try:
            self.pwm.stop()
        except:
            pass


class MotorController:
    def __init__(self, config_path):
        GPIO.setmode(GPIO.BCM)
        with open(config_path, "r") as f:
            cfg = json.load(f)

        self.stby = cfg["STBY"]
        GPIO.setup(self.stby, GPIO.OUT)
        GPIO.output(self.stby, GPIO.HIGH)

        L = cfg["LEFT"]
        R = cfg["RIGHT"]

        self.left_motor = Motor(L["AIN1"], L["AIN2"], L["PWM"])
        self.right_motor = Motor(R["BIN1"], R["BIN2"], R["PWM"])

    def forward(self, speed=50):
        self.left_motor.forward(speed)
        self.right_motor.forward(speed)

    def backward(self, speed=50):
        self.left_motor.backward(speed)
        self.right_motor.backward(speed)

    def turn_left(self, speed=50):
        self.left_motor.backward(speed)
        self.right_motor.forward(speed)

    def turn_right(self, speed=50):
        self.left_motor.forward(speed)
        self.right_motor.backward(speed)

    def stop(self):
        self.left_motor.stop()
        self.right_motor.stop()

    def cleanup(self):
        self.left_motor.cleanup()
        self.right_motor.cleanup()
        GPIO.cleanup()


if __name__ == "__main__":
    motor = MotorController("motorConfig.json")
    try:
        motor.forward(60)
        time.sleep(2)
        motor.backward(60)
        time.sleep(2)
        motor.turn_left(60)
        time.sleep(1)
        motor.turn_right(60)
        time.sleep(1)
        motor.stop()
    finally:
        motor.cleanup()
