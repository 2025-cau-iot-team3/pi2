#include <wiringPi.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <json-c/json.h>

// 속도( -100 ~ 100 ) → PWM (0~1023)
int mapSpeed(int speed) {
    if (speed > 100) speed = 100;
    if (speed < -100) speed = -100;
    return abs(speed) * 1023 / 100;
}

int main(int argc, char *argv[]) {

    // ---- 인자 파싱 ----
    int left_speed = 0;
    int right_speed = 0;

    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--left") == 0 && i + 1 < argc) {
            left_speed = atoi(argv[++i]);
        } else if (strcmp(argv[i], "--right") == 0 && i + 1 < argc) {
            right_speed = atoi(argv[++i]);
        }
    }

    printf("[CMD] LEFT=%d, RIGHT=%d\n", left_speed, right_speed);

    // ---- motorConfig.json 로드 ----
    FILE *fp = fopen("motorConfig.json", "r");
    if (!fp) {
        printf("ERROR: motorConfig.json not found\n");
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

    printf("[CFG] LEFT : IN1=%d IN2=%d PWM=%d\n", L_IN1, L_IN2, L_PWM);
    printf("[CFG] RIGHT: IN1=%d IN2=%d PWM=%d\n", R_IN1, R_IN2, R_PWM);

    // ---- wiringPi ----
    wiringPiSetup();

    pinMode(L_IN1, OUTPUT);
    pinMode(L_IN2, OUTPUT);
    pinMode(L_PWM, PWM_OUTPUT);

    pinMode(R_IN1, OUTPUT);
    pinMode(R_IN2, OUTPUT);
    pinMode(R_PWM, PWM_OUTPUT);

    // ---- LEFT 모터 ----
    if (left_speed > 0) {
        digitalWrite(L_IN1, HIGH);
        digitalWrite(L_IN2, LOW);
    } else if (left_speed < 0) {
        digitalWrite(L_IN1, LOW);
        digitalWrite(L_IN2, HIGH);
    } else {
        digitalWrite(L_IN1, LOW);
        digitalWrite(L_IN2, LOW);
    }

    pwmWrite(L_PWM, mapSpeed(left_speed));

    // ---- RIGHT 모터 ----
    if (right_speed > 0) {
        digitalWrite(R_IN1, HIGH);
        digitalWrite(R_IN2, LOW);
    } else if (right_speed < 0) {
        digitalWrite(R_IN1, LOW);
        digitalWrite(R_IN2, HIGH);
    } else {
        digitalWrite(R_IN1, LOW);
        digitalWrite(R_IN2, LOW);
    }

    pwmWrite(R_PWM, mapSpeed(right_speed));

    printf("[INFO] Motors running (infinite until next command)\n");

    // 무한 지속 → 다음 명령 들어오면 새로운 값으로 실행됨
    while (1) {
        usleep(100000);
    }

    return 0;
}
