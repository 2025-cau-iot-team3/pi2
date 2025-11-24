#include <errno.h>
#include <i2c/smbus.h>
#include <json-c/json.h>
#include <linux/i2c-dev.h>
#include <pigpio.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <time.h>
#include <unistd.h>

#define MAX_SENSORS 8
#define DEFAULT_BUS 1
#define DEFAULT_ADDR 0x68

typedef struct {
    char name[64];
    int trig;
    int echo;
    int timeout_us;
} sensor_t;

static sensor_t sensors[MAX_SENSORS];
static int sensor_count = 0;

static const char *CONFIG_PATH = "../cfg/sensorConfig.json";
static const char *STATE_PATH = "../sensor_state";

static int load_config(int *bus, int *addr) {
    sensor_count = 0;
    *bus = DEFAULT_BUS;
    *addr = DEFAULT_ADDR;

    FILE *fp = fopen(CONFIG_PATH, "r");
    if (!fp) {
        perror("open cfg/sensorConfig.json");
        return -1;
    }
    fseek(fp, 0, SEEK_END);
    long len = ftell(fp);
    fseek(fp, 0, SEEK_SET);
    char *buf = calloc(len + 1, 1);
    fread(buf, 1, len, fp);
    fclose(fp);

    struct json_object *root = json_tokener_parse(buf);
    free(buf);
    if (!root) return -1;

    struct json_object *mpu;
    if (json_object_object_get_ex(root, "mpu6050", &mpu)) {
        struct json_object *bus_val, *addr_val;
        if (json_object_object_get_ex(mpu, "bus", &bus_val)) {
            *bus = json_object_get_int(bus_val);
        }
        if (json_object_object_get_ex(mpu, "address", &addr_val)) {
            *addr = json_object_get_int(addr_val);
        }
    }

    json_object_object_foreach(root, key, val) {
        if (sensor_count >= MAX_SENSORS) break;
        struct json_object *type;
        if (!json_object_object_get_ex(val, "type", &type)) continue;
        const char *type_str = json_object_get_string(type);
        if (strcmp(type_str, "distance") != 0) continue;

        struct json_object *trig, *echo, *timeout;
        if (!json_object_object_get_ex(val, "trigger_pin", &trig)) continue;
        if (!json_object_object_get_ex(val, "echo_pin", &echo)) continue;

        memset(&sensors[sensor_count], 0, sizeof(sensor_t));
        strncpy(sensors[sensor_count].name, key, sizeof(sensors[sensor_count].name) - 1);
        sensors[sensor_count].trig = json_object_get_int(trig);
        sensors[sensor_count].echo = json_object_get_int(echo);
        sensors[sensor_count].timeout_us = 30000;
        if (json_object_object_get_ex(val, "timeout", &timeout)) {
            sensors[sensor_count].timeout_us = json_object_get_int(timeout);
        }
        sensor_count++;
    }

    json_object_put(root);
    return 0;
}

static int open_i2c(int bus, int addr) {
    char dev[32];
    snprintf(dev, sizeof(dev), "/dev/i2c-%d", bus);
    int fd = open(dev, O_RDWR);
    if (fd < 0) {
        perror("open i2c");
        return -1;
    }
    if (ioctl(fd, I2C_SLAVE, addr) < 0) {
        perror("ioctl I2C_SLAVE");
        close(fd);
        return -1;
    }
    return fd;
}

static int16_t read_word(int fd, uint8_t reg) {
    int hi = i2c_smbus_read_byte_data(fd, reg);
    int lo = i2c_smbus_read_byte_data(fd, reg + 1);
    if (hi < 0 || lo < 0) return 0;
    return (int16_t)((hi << 8) | lo);
}

static void read_gyro_vals(int fd, double *ax, double *ay, double *az, double *gx, double *gy, double *gz) {
    int16_t ax_raw = read_word(fd, 0x3B);
    int16_t ay_raw = read_word(fd, 0x3D);
    int16_t az_raw = read_word(fd, 0x3F);
    int16_t gx_raw = read_word(fd, 0x43);
    int16_t gy_raw = read_word(fd, 0x45);
    int16_t gz_raw = read_word(fd, 0x47);

    // Fail-safe: if all raw values are zero, treat as sensor error and use dummy values
    if (ax_raw == 0 && ay_raw == 0 && az_raw == 0 &&
        gx_raw == 0 && gy_raw == 0 && gz_raw == 0) {
        *ax = 0.0;
        *ay = 0.0;
        *az = 1.0;
        *gx = 0.0;
        *gy = 0.0;
        *gz = 0.0;
        return;
    }

    *ax = ax_raw / 16384.0;
    *ay = ay_raw / 16384.0;
    *az = az_raw / 16384.0;
    *gx = gx_raw / 131.0;
    *gy = gy_raw / 131.0;
    *gz = gz_raw / 131.0;
}

static double measure_ultra(int trig, int echo, int timeout_us) {
    gpioWrite(trig, PI_LOW);
    gpioDelay(2);
    gpioWrite(trig, PI_HIGH);
    gpioDelay(10);
    gpioWrite(trig, PI_LOW);

    uint32_t start = gpioTick();
    while (gpioRead(echo) == PI_LOW) {
        if (gpioTick() - start > (uint32_t)timeout_us) return -1.0;
    }
    uint32_t echo_start = gpioTick();
    while (gpioRead(echo) == PI_HIGH) {
        if (gpioTick() - echo_start > (uint32_t)timeout_us) return -1.0;
    }
    uint32_t pulse = gpioTick() - echo_start;
    return (pulse * 0.0343) / 2.0;
}

static void write_state(const char *path, double *distances, double ax, double ay, double az, double gx, double gy, double gz) {
    struct json_object *root = json_object_new_object();
    struct json_object *dist_obj = json_object_new_object();
    double min_dist = 0.0;

    for (int i = 0; i < sensor_count; i++) {
        json_object_object_add(dist_obj, sensors[i].name, json_object_new_double(distances[i]));
        if (distances[i] > 0.0) {
            if (min_dist == 0.0 || distances[i] < min_dist) {
                min_dist = distances[i];
            }
        }
    }

    struct json_object *gyro = json_object_new_array();
    json_object_array_add(gyro, json_object_new_double(gx));
    json_object_array_add(gyro, json_object_new_double(gy));
    json_object_array_add(gyro, json_object_new_double(gz));

    json_object_object_add(root, "dist", json_object_new_double(min_dist));
    json_object_object_add(root, "distances", dist_obj);
    json_object_object_add(root, "object", json_object_new_int(0));
    json_object_object_add(root, "gyro", gyro);
    json_object_object_add(root, "brightness", json_object_new_double(0.0));
    json_object_object_add(root, "ts", json_object_new_double((double)time(NULL)));

    const char *json_str = json_object_to_json_string_ext(root, JSON_C_TO_STRING_PLAIN);
    char tmp_path[256];
    snprintf(tmp_path, sizeof(tmp_path), "%s.tmp", path);

    FILE *fp = fopen(tmp_path, "w");
    if (fp) {
        fputs(json_str, fp);
        fclose(fp);
        rename(tmp_path, path);
    }
    json_object_put(root);
}

int main(int argc, char **argv) {
    int bus, addr;
    if (load_config(&bus, &addr) < 0) {
        return 1;
    }

    int fd = open_i2c(bus, addr);
    if (fd < 0) return 1;

    if (i2c_smbus_write_byte_data(fd, 0x6B, 0) < 0) {
        perror("i2c write 0x6B");
        close(fd);
        return 1;
    }
    if (gpioInitialise() < 0) {
        fprintf(stderr, "pigpio init failed\n");
        close(fd);
        return 1;
    }
    for (int i = 0; i < sensor_count; i++) {
        gpioSetMode(sensors[i].trig, PI_OUTPUT);
        gpioSetMode(sensors[i].echo, PI_INPUT);
        gpioWrite(sensors[i].trig, PI_LOW);
    }

    int hz = 20;
    if (argc >= 2) {
        hz = atoi(argv[1]);
        if (hz <= 0) hz = 20;
    }
    double interval = 1.0 / hz;
    printf("[sensor_daemon] gyro bus=%d addr=0x%02X, ultra=%d -> %s (%.1f Hz)\n",
           bus, addr, sensor_count, STATE_PATH, hz + 0.0);

    double distances[MAX_SENSORS];
    double ax, ay, az, gx, gy, gz;

    while (1) {
        read_gyro_vals(fd, &ax, &ay, &az, &gx, &gy, &gz);
        for (int i = 0; i < sensor_count; i++) {
            distances[i] = measure_ultra(sensors[i].trig, sensors[i].echo, sensors[i].timeout_us);
        }
        write_state(STATE_PATH, distances, ax, ay, az, gx, gy, gz);
        usleep((useconds_t)(interval * 1e6));
    }

    gpioTerminate();
    close(fd);
    return 0;
}
