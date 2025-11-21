import smbus
import time

bus = smbus.SMBus(1)
addr = 0x68

# MPU6050 wake (exit sleep mode)
bus.write_byte_data(addr, 0x6B, 0)

def read_word(reg):
    h = bus.read_byte_data(addr, reg)
    l = bus.read_byte_data(addr, reg + 1)
    v = (h << 8) + l
    if v >= 0x8000:
        v = -((65535 - v) + 1)
    return v

def read():
    ax = read_word(0x3B) / 16384.0
    ay = read_word(0x3D) / 16384.0
    az = read_word(0x3F) / 16384.0

    gx = read_word(0x43) / 131.0
    gy = read_word(0x45) / 131.0
    gz = read_word(0x47) / 131.0

    acc = (ax, ay, az)
    gyro = (gx, gy, gz)
    return acc, gyro

if __name__ == "__main__":
    while True:
        acc, gyro = read()
        ax, ay, az = acc
        gx, gy, gz = gyro
        print(f"ACC: {ax:.2f} {ay:.2f} {az:.2f}   GYRO: {gx:.2f} {gy:.2f} {gz:.2f}")
        time.sleep(0.2)
