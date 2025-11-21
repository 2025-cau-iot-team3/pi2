#include <stdio.h>
#include <string.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    int left_speed = 0;
    int right_speed = 0;

    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--left") == 0 && i + 1 < argc) {
            left_speed = atoi(argv[++i]);
        } else if (strcmp(argv[i], "--right") == 0 && i + 1 < argc) {
            right_speed = atoi(argv[++i]);
        }
    }

    FILE *fp = fopen("motor_cmd", "w");
    if (!fp) {
        printf("ERROR: cannot write motor_cmd\n");
        return 1;
    }

    fprintf(fp, "%d %d\n", left_speed, right_speed);
    fclose(fp);

    return 0;
}
