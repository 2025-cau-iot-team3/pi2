#include <pigpio.h>
#include <stdio.h>
#include <json-c/json.h>
#include <unistd.h>
#include <stdlib.h>

// ------------------------------------------------------
// speed -100~100  → duty 0~1,000,000 변환 (DC 모터)
// ------------------------------------------------------
int speedToDuty(int s) {
    if (s > 100) s = 100;
    if (s < -100) s = -100;
    return abs(s) * 1000000 / 100;   // 0~1,000,000
}

// ------------------------------------------------------
// angle 0~180° → servo pulsewidth 500~2500us 변환
// ------------------------------------------------------
int angleToPulse(int angle) {
    if (angle < 0) angle = 0;
    if (angle > 180) angle = 180;
    return 500 + (angle * 2000 / 180);  // 500~2500us
}

int main() {

    // ---------------------- config 읽기 ----------------------
    FILE *fp = fopen("../cfg/robotConfig.json", "r");
    if (!fp) {
        printf("ERROR: robotConfig.json not found\n");
        return 1;
    }

    char buffer[4096];
    fread(buffer, 1, sizeof(buffer), fp);
    fclose(fp);

    struct json_object *root = json_tokener_parse(buffer);

    // ---------------------- 모터 핀 로드 ----------------------
    struct json_object *ml = json_object_object_get(root, "MOTOR_LEFT");
    struct json_object *mr = json_object_object_get(root, "MOTOR_RIGHT");

    int L_IN1 = json_object_get_int(json_object_object_get(ml, "IN1"));
    int L_IN2 = json_object_get_int(json_object_object_get(ml, "IN2"));
    int L_PWM = json_object_get_int(json_object_object_get(ml, "PWM"));

    int R_IN1 = json_object_get_int(json_object_object_get(mr, "IN1"));
    int R_IN2 = json_object_get_int(json_object_object_get(mr, "IN2"));
    int R_PWM = json_object_get_int(json_object_object_get(mr, "PWM"));

    // ---------------------- 서보 PIN 로드 ----------------------
    int SERVO_L = json_object_get_int(json_object_object_get(
                        json_object_object_get(root, "SERVO_LEFT"),
                        "PIN"));

    int SERVO_R = json_object_get_int(json_object_object_get(
                        json_object_object_get(root, "SERVO_RIGHT"),
                        "PIN"));

    printf("[DAEMON] Config Loaded.\n");

    // ---------------------- pigpio INIT ----------------------
    if (gpioInitialise() < 0) {
        printf("ERROR: pigpio init failed\n");
        return 1;
    }

    printf("[DAEMON] pigpio initialised.\n");

    // 모터 PIN 설정
    gpioSetMode(L_IN1, PI_OUTPUT);
    gpioSetMode(L_IN2, PI_OUTPUT);
    gpioSetMode(L_PWM, PI_OUTPUT);

    gpioSetMode(R_IN1, PI_OUTPUT);
    gpioSetMode(R_IN2, PI_OUTPUT);
    gpioSetMode(R_PWM, PI_OUTPUT);

    // 서보 PIN 출력
    gpioSetMode(SERVO_L, PI_OUTPUT);
    gpioSetMode(SERVO_R, PI_OUTPUT);

    int left_speed = 0, right_speed = 0;
    int servo_L_angle = 90, servo_R_angle = 90;

    printf("[DAEMON] Watching motor_cmd & servo_cmd...\n");

    // ======================= MAIN LOOP =======================
    while (1) {

        // ----------- motor_cmd 읽기 ----------------
        FILE *m = fopen("motor_cmd", "r");
        if (m) {
            fscanf(m, "%d %d", &left_speed, &right_speed);
            fclose(m);
        }

        // ----------- servo_cmd 읽기 ----------------
        FILE *s = fopen("servo_cmd", "r");
        if (s) {
            fscanf(s, "%d %d", &servo_L_angle, &servo_R_angle);
            fclose(s);
        }

        // ======================= LEFT MOTOR (INVERTED) =======================
        if (left_speed > 0) {
            gpioWrite(L_IN1, 0);  // 반전됨
            gpioWrite(L_IN2, 1);  // 반전됨
            gpioHardwarePWM(L_PWM, 20000, speedToDuty(left_speed));
        } else if (left_speed < 0) {
            gpioWrite(L_IN1, 1);  // 반전됨
            gpioWrite(L_IN2, 0);  // 반전됨
            gpioHardwarePWM(L_PWM, 20000, speedToDuty(left_speed));
        } else {
            gpioWrite(L_IN1, 0);
            gpioWrite(L_IN2, 0);
            gpioHardwarePWM(L_PWM, 20000, 0);
        }

        // ======================= RIGHT MOTOR (NORMAL) =======================
        if (right_speed > 0) {
            gpioWrite(R_IN1, 1);
            gpioWrite(R_IN2, 0);
            gpioHardwarePWM(R_PWM, 20000, speedToDuty(right_speed));
        } else if (right_speed < 0) {
            gpioWrite(R_IN1, 0);
            gpioWrite(R_IN2, 1);
            gpioHardwarePWM(R_PWM, 20000, speedToDuty(right_speed));
        } else {
            gpioWrite(R_IN1, 0);
            gpioWrite(R_IN2, 0);
            gpioHardwarePWM(R_PWM, 20000, 0);
        }

        // ======================= SERVOS =======================
        gpioServo(SERVO_L, angleToPulse(servo_L_angle));
        gpioServo(SERVO_R, angleToPulse(servo_R_angle));

        usleep(20000);  // 20ms loop
    }

    gpioTerminate();
    return 0;
}
