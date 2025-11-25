#include <pigpio.h>
#include <stdio.h>
#include <json-c/json.h>
#include <unistd.h>
#include <stdlib.h>

// 속도 -100 ~ 100 → duty 0~1,000,000 변환
int speedToDuty(int s) {
    if (s > 100) s = 100;
    if (s < -100) s = -100;
    return abs(s) * 1000000 / 100;
}

int main() {
    // ------------------ motorConfig.json 읽기 ------------------
<<<<<<< HEAD
    FILE *fp = fopen("motorConfig.json", "r");
    if (!fp) {
        printf("ERROR: motorConfig.json not found\n");
=======
    FILE *fp = fopen("../cfg/motorConfig.json", "r");
    if (!fp) {
        printf("ERROR: cfg/motorConfig.json not found\n");
>>>>>>> feat/sensor
        return 1;
    }

    char buffer[4096];
    fread(buffer, 1, sizeof(buffer), fp);
    fclose(fp);

    struct json_object *root = json_tokener_parse(buffer);

    struct json_object *left  = json_object_object_get(root, "LEFT");
    struct json_object *right = json_object_object_get(root, "RIGHT");

    int L_IN1 = json_object_get_int(json_object_object_get(left, "IN1"));
    int L_IN2 = json_object_get_int(json_object_object_get(left, "IN2"));
    int L_PWM = json_object_get_int(json_object_object_get(left, "PWM"));

    int R_IN1 = json_object_get_int(json_object_object_get(right, "IN1"));
    int R_IN2 = json_object_get_int(json_object_object_get(right, "IN2"));
    int R_PWM = json_object_get_int(json_object_object_get(right, "PWM"));

    printf("[DAEMON] Loaded pins.\n");

    // ------------------ pigpio 초기화 ------------------
    if (gpioInitialise() < 0) {
        printf("ERROR: pigpio init failed\n");
        return 1;
    }
    printf("[DAEMON] pigpio initialised.\n");

    gpioSetMode(L_IN1, PI_OUTPUT);
    gpioSetMode(L_IN2, PI_OUTPUT);
    gpioSetMode(L_PWM,  PI_OUTPUT);

    gpioSetMode(R_IN1, PI_OUTPUT);
    gpioSetMode(R_IN2, PI_OUTPUT);
    gpioSetMode(R_PWM,  PI_OUTPUT);

    printf("[DAEMON] Watching motor_cmd...\n");

    int left_speed = 0;
    int right_speed = 0;

    while (1) {
        FILE *cmd = fopen("motor_cmd", "r");
        if (cmd) {
            int l, r;
            if (fscanf(cmd, "%d %d", &l, &r) == 2) {
                left_speed = l;
                right_speed = r;
            }
            fclose(cmd);
        }

        // ========================= LEFT =========================
        if (left_speed > 0) {
            gpioWrite(L_IN1, 1);
            gpioWrite(L_IN2, 0);
            gpioHardwarePWM(L_PWM, 20000, speedToDuty(left_speed));
        } else if (left_speed < 0) {
            gpioWrite(L_IN1, 0);
            gpioWrite(L_IN2, 1);
            gpioHardwarePWM(L_PWM, 20000, speedToDuty(left_speed));
        } else {
            // 완전 정지 → 브레이크/코스트 노이즈 제거
            gpioWrite(L_IN1, 0);
            gpioWrite(L_IN2, 0);
            gpioHardwarePWM(L_PWM, 20000, 0);
        }

        // ========================= RIGHT =========================
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

        usleep(20000); // 20ms
    }

    gpioTerminate();
    return 0;
}
