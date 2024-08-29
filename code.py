import board
import time
import busio
from adafruit_bus_device.i2c_device import I2CDevice
from mpu6886 import MPU6886
import struct
import busio  # type: ignore (This too!)
from joystick_xl.inputs import Axis, Button, Hat
from joystick_xl.joystick import Joystick
from joystick import JoystickUnit

# Axis configuration constants
AXIS_DB = 3 # Deadband to apply to axis center points.
AXIS_MIN = -127  # Minimum raw axis value.
AXIS_MAX = 127 # Maximum raw axis value.

# Axis configuration constants
ACCEL_DB = 10 # Deadband to apply to axis center points.
ACCEL_MIN = -100  # Minimum raw axis value.
ACCEL_MAX = 100 # Maximum raw axis value.


# IMU6866 define
MPU6886_ADDRESS=0x68

i2c = busio.I2C(board.IMU_SCL, board.IMU_SDA)
i2c2 = busio.I2C(board.D1, board.D2)
imu = I2CDevice(i2c, MPU6886_ADDRESS)
lcd = board.DISPLAY

jhat = JoystickUnit(i2c2, 0x52)
jhat.swap_x(1)

sensor = MPU6886(i2c)

hotas = Joystick()

hotas.add_input(
    Button(),
    Axis(deadband=AXIS_DB, min=AXIS_MIN, max=AXIS_MAX),
    Axis(deadband=AXIS_DB, min=AXIS_MIN, max=AXIS_MAX),
    Axis(deadband=ACCEL_DB, min=ACCEL_MIN, max=ACCEL_MAX),
    Axis(deadband=ACCEL_DB, min=ACCEL_MIN, max=ACCEL_MAX),
)

print(sensor.gyro())

while True:
    gyro_array = sensor.gyro()
    accel_array = sensor.acceleration()
    hotas.axis[0].source_value = int(accel_array[0]*10)
    hotas.axis[1].source_value = int(accel_array[1]*10)
    hotas.axis[2].source_value = jhat.get_x()
    hotas.axis[3].source_value = jhat.get_y()
    hotas.button[0].source_value = 1 - jhat.get_button_status()
    hotas.update()
    print(jhat.get_x())
    print(accel_array)
    time.sleep(0.1)
