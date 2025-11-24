#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <time.h>
#include <sys/ioctl.h>

#include <linux/i2c-dev.h>
#include <linux/i2c.h>

#include <pigpio.h>
#include <json-c/json.h>

#define MAX_SENSORS 8
#define STATE_PATH "./sensor_state"

/* ======================= SENSOR STRUCT ======================= */

typedef struct {
    char name[32];
    int trig;
    int echo;
    int timeout_us;
} sensor_t;

static sensor_t sensors[MAX_SENSORS];
static int sensor_count = 0;

/* ======================= SMBUS REPLACEMENTS ======================= */

static int read_byte_data(int fd, uint8_t reg)
{
    struct i2c_smbus_ioctl_data args;
    union i2c_smbus_data data;

    args.read_write = I2C_SMBUS_READ;
    args.command = reg;
    args.size = I2C_SMBUS_BYTE_DATA;
    args.data = &data;

    if (ioctl(fd, I2C_SMBUS, &args) < 0)
        return -1;

    return data.byte;
}

static int write_byte_data(int fd, uint8_t reg, uint8_t value)
{
    struct i2c_smbus_ioctl_data args;
    union i2c_smbus_data data;

    data.byte = value;
    args.read_write = I2C_SMBUS_WRITE;
    args.command = reg;
    args.size = I2C_SMBUS_BYTE_DATA;
    args.data = &data;

    return ioctl(fd, I2C_SMBUS, &args);
}

static int16_t read_word_new(int fd, uint8_t reg)
{
    int hi = read_byte_data(fd, reg);
    int lo = read_byte_data(fd, reg + 1);
    if (hi < 0 || lo < 0)
        return 0;
    return (int16_t)((hi << 8) | lo);
}

/* ======================== CONFIG LOADING ========================= */

static int load_config(int *bus, int *addr)
{
    FILE *fp = fopen("../cfg/sensorConfig.json", "r");
    if (!fp) return -1;

    fseek(fp, 0, SEEK_END);
    long sz = ftell(fp);
    fseek(fp, 0, SEEK_SET);

    char *buf = malloc(sz + 1);
    fread(buf, 1, sz, fp);
    buf[sz] = 0;
    fclose(fp);

    struct json_object *root = json_tokener_parse(buf);
    free(buf);
    if (!root) return -1;

    struct json_object *mpu;
    if (json_object_object_get_ex(root, "mpu6050", &mpu)) {
        struct json_object *bus_v, *addr_v;
        json_object_object_get_ex(mpu, "bus", &bus_v);
        json_object_object_get_ex(mpu, "address", &addr_v);
        *bus = json_object_get_int(bus_v);
        *addr = json_object_get_int(addr_v);
    }

    json_object_object_foreach(root, key, val) {
        if (sensor_count >= MAX_SENSORS) break;

        struct json_object *type;
        if (!json_object_object_get_ex(val, "type", &type)) continue;
        if (strcmp(json_object_get_string(type), "distance") != 0) continue;

        struct json_object *tr, *ec;
        if (!json_object_object_get_ex(val, "trigger_pin", &tr)) continue;
        if (!json_object_object_get_ex(val, "echo_pin", &ec)) continue;

        memset(&sensors[sensor_count], 0, sizeof(sensor_t));
        strncpy(sensors[sensor_count].name, key, 31);
        sensors[sensor_count].trig = json_object_get_int(tr);
        sensors[sensor_count].echo = json_object_get_int(ec);
        sensors[sensor_count].timeout_us = 30000;

        sensor_count++;
    }

    json_object_put(root);
    return 0;
}

/* ========================== I2C OPEN =========================== */

static int open_i2c(int bus, int addr)
{
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

/* ========================== GYRO READ =========================== */

static void read_gyro_vals(int fd, double *ax, double *ay, double *az,
                           double *gx, double *gy, double *gz)
{
    int16_t ax_raw = read_word_new(fd, 0x3B);
    int16_t ay_raw = read_word_new(fd, 0x3D);
    int16_t az_raw = read_word_new(fd, 0x3F);
    int16_t gx_raw = read_word_new(fd, 0x43);
    int16_t gy_raw = read_word_new(fd, 0x45);
    int16_t gz_raw = read_word_new(fd, 0x47);

    if (ax_raw == 0 && ay_raw == 0 && az_raw == 0 &&
        gx_raw == 0 && gy_raw == 0 && gz_raw == 0)
    {
        *ax = 0.0; *ay = 0.0; *az = 1.0;
        *gx = 0.0; *gy = 0.0; *gz = 0.0;
        return;
    }

    *ax = ax_raw / 16384.0;
    *ay = ay_raw / 16384.0;
    *az = az_raw / 16384.0;
    *gx = gx_raw / 131.0;
    *gy = gy_raw / 131.0;
    *gz = gz_raw / 131.0;
}

/* ====================== ULTRASONIC READ ========================= */

static double measure_ultra(int trig, int echo, int timeout_us)
{
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

/* ============================ JSON ============================== */

static void write_state(const char *path, double *dist,
                        double ax, double ay, double az,
                        double gx, double gy, double gz)
{
    struct json_object *root = json_object_new_object();

    for (int i = 0; i < sensor_count; i++) {
        json_object_object_add(root,
                               sensors[i].name,
                               json_object_new_double(dist[i]));
    }

    struct json_object *gyro = json_object_new_array();
    json_object_array_add(gyro, json_object_new_double(gx));
    json_object_array_add(gyro, json_object_new_double(gy));
    json_object_array_add(gyro, json_object_new_double(gz));
    json_object_object_add(root, "gyro", gyro);

    json_object_object_add(root, "ts",
                           json_object_new_int64((int64_t)time(NULL)));

    char tmp[256];
    snprintf(tmp, sizeof(tmp), "%s.tmp", path);

    FILE *fp = fopen(tmp, "w");
    if (fp) {
        fputs(json_object_to_json_string_ext(root,
              JSON_C_TO_STRING_PLAIN), fp);
        fclose(fp);
        rename(tmp, path);
    }

    json_object_put(root);
}

/* ============================== MAIN ============================ */

int main(int argc, char **argv)
{
    int bus = 1, addr = 0x68;

    if (load_config(&bus, &addr) < 0) {
        fprintf(stderr, "Failed to load config\n");
        return 1;
    }

    int fd = open_i2c(bus, addr);
    if (fd < 0) return 1;

    if (write_byte_data(fd, 0x6B, 0) < 0) {
        perror("i2c write 0x6B");
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

    printf("[sensor_daemon] gyro bus=%d addr=0x%02X, ultra=%d -> %s (%d Hz)\n",
           bus, addr, sensor_count, STATE_PATH, hz);

    double dist[MAX_SENSORS];
    double ax, ay, az, gx, gy, gz;

    while (1) {
        read_gyro_vals(fd, &ax, &ay, &az, &gx, &gy, &gz);

        for (int i = 0; i < sensor_count; i++)
            dist[i] = measure_ultra(sensors[i].trig,
                                    sensors[i].echo,
                                    sensors[i].timeout_us);

        write_state(STATE_PATH, dist,
                     ax, ay, az,
                     gx, gy, gz);

        usleep((useconds_t)(interval * 1e6));
    }

    gpioTerminate();
    close(fd);
    return 0;
}
