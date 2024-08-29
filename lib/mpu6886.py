import board
import busio
import time

class MPU6886:
    # MPU6886 Register Addresses and Configuration Constants
    _CONFIG = 0x1a
    _GYRO_CONFIG = 0x1b
    _ACCEL_CONFIG = 0x1c
    _ACCEL_CONFIG2 = 0x1d
    _ACCEL_XOUT_H = 0x3b
    _ACCEL_XOUT_L = 0x3c
    _ACCEL_YOUT_H = 0x3d
    _ACCEL_YOUT_L = 0x3e
    _ACCEL_ZOUT_H = 0x3f
    _ACCEL_ZOUT_L = 0x40
    _TEMP_OUT_H = 0x41
    _TEMP_OUT_L = 0x42
    _GYRO_XOUT_H = 0x43
    _GYRO_XOUT_L = 0x44
    _GYRO_YOUT_H = 0x45
    _GYRO_YOUT_L = 0x46
    _GYRO_ZOUT_H = 0x47
    _GYRO_ZOUT_L = 0x48
    _PWR_MGMT_1 = 0x6b
    _WHO_AM_I = 0x75

    # Accelerometer Full-Scale Selection Settings
    ACCEL_FS_SEL_2G = 0b00000000
    ACCEL_FS_SEL_4G = 0b00001000
    ACCEL_FS_SEL_8G = 0b00010000
    ACCEL_FS_SEL_16G = 0b00011000

    # Accelerometer Sensitivity (LSB/g)
    _ACCEL_SO_2G = 16384
    _ACCEL_SO_4G = 8192
    _ACCEL_SO_8G = 4096
    _ACCEL_SO_16G = 2048

    # Gyroscope Full-Scale Selection Settings (DPS: Degrees Per Second)
    GYRO_FS_SEL_250DPS = 0b00000000
    GYRO_FS_SEL_500DPS = 0b00001000
    GYRO_FS_SEL_1000DPS = 0b00010000
    GYRO_FS_SEL_2000DPS = 0b00011000

    # Gyroscope Sensitivity (LSB/DPS)
    _GYRO_SO_250DPS = 131
    _GYRO_SO_500DPS = 62.5
    _GYRO_SO_1000DPS = 32.8
    _GYRO_SO_2000DPS = 16.4

    # Temperature Sensor Calibration
    _TEMP_SO = 326.8
    _TEMP_OFFSET = 25

    # Scale Factors
    SF_G = 1
    SF_M_S2 = 9.80665
    SF_DEG_S = 1
    SF_RAD_S = 0.017453292519943

    def __init__(self, i2c_bus, address=0x68):
        self.i2c = i2c_bus
        self.address = address

        self._initialize_sensor()

    def _initialize_sensor(self):
        self._write_register(self._PWR_MGMT_1, 0b10000000)  # Reset
        time.sleep(0.1)
        self._write_register(self._PWR_MGMT_1, 0b00000001)  # Set clock source

        self._write_register(self._ACCEL_CONFIG, self.ACCEL_FS_SEL_2G)  # Set accelerometer range
        self._write_register(self._GYRO_CONFIG, self.GYRO_FS_SEL_250DPS)  # Set gyroscope range

    def _write_register(self, register, value):
        while not self.i2c.try_lock():
            pass
        try:
            self.i2c.writeto(self.address, bytes([register, value]))
        finally:
            self.i2c.unlock()

    def _read_register(self, register, length):
        while not self.i2c.try_lock():
            pass
        try:
            self.i2c.writeto(self.address, bytes([register]))
            data = bytearray(length)
            self.i2c.readfrom_into(self.address, data)
            return data
        finally:
            self.i2c.unlock()

    def acceleration(self):
        data = self._read_register(self._ACCEL_XOUT_H, 6)
        ax = self._combine_bytes(data[0], data[1]) / self._ACCEL_SO_2G * self.SF_M_S2
        ay = self._combine_bytes(data[2], data[3]) / self._ACCEL_SO_2G * self.SF_M_S2
        az = self._combine_bytes(data[4], data[5]) / self._ACCEL_SO_2G * self.SF_M_S2
        return (ax, ay, az)

    def gyro(self):
        data = self._read_register(self._GYRO_XOUT_H, 6)
        gx = self._combine_bytes(data[0], data[1]) / self._GYRO_SO_250DPS  # Adjust sensitivity factor based on your configuration
        gy = self._combine_bytes(data[2], data[3]) / self._GYRO_SO_250DPS
        gz = self._combine_bytes(data[4], data[5]) / self._GYRO_SO_250DPS
        return (gx, gy, gz)

    def temperature(self):
        data = self._read_register(self._TEMP_OUT_H, 2)
        temp_raw = self._combine_bytes(data[0], data[1])
        temperature = (temp_raw / self._TEMP_SO) + self._TEMP_OFFSET
        return temperature

    def _combine_bytes(self, high_byte, low_byte):
        value = (high_byte << 8) | low_byte
        if value & 0x8000:
            value -= 65536
        return value
