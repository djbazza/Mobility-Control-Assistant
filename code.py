# SPDX-FileCopyrightText: 2024 Michał Pokusa
#
# SPDX-License-Identifier: Unlicense

import socketpool
import wifi
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

from adafruit_httpserver import Server, Route, as_route, REQUEST_HANDLED_RESPONSE_SENT, Request, Response, GET, POST

AP_SSID = "MC"
AP_PASSWORD = "helpmemove"

print("Creating access point...")
wifi.radio.start_ap(ssid=AP_SSID, password=AP_PASSWORD)
print(f"Created access point {AP_SSID}")

pool = socketpool.SocketPool(wifi.radio)
server = Server(pool, "/static", debug=True)

sampling_ms = 150
minChange = 5

# Axis configuration constants
AXIS_DB = 5
AXIS_MIN = -255  # Minimum raw axis value.
AXIS_MAX = 255 # Maximum raw axis value.
factor = 25

# Axis configuration constants
THUMB_MIN = -128  # Minimum raw axis value.
THUMB_MAX = 128 # Maximum raw axis value.
THUMB_DB = 0 # Deadband to apply to axis center points.

# IMU6866 define
MPU6886_ADDRESS=0x68

i2c = busio.I2C(board.IMU_SCL, board.IMU_SDA)
i2c2 = busio.I2C(board.D1, board.D2)
imu = I2CDevice(i2c, MPU6886_ADDRESS)
lcd = board.DISPLAY
jhat = ""
assert i2c2.try_lock()
if 0x52 in i2c2.scan():
    i2c2.unlock()
    jhat = JoystickUnit(i2c2, 0x52)
    jhat.swap_x(1)

sensor = MPU6886(i2c)

hotas = Joystick()

hotas.add_input(
    Button(),
    Axis(deadband=125, min=-255, max=255),
    Axis(deadband=125, min=-255, max=255),
    Axis(deadband=THUMB_DB, min=THUMB_MIN, max=THUMB_MAX),
    Axis(deadband=THUMB_DB, min=THUMB_MIN, max=THUMB_MAX),
)


FORM_HTML_TEMPLATE = """
<html lang="en">
    <head>
        <title>Form with {enctype} enctype</title>
    </head>
    <body>
        <h2>Please adjust the Joystick Settings</h2>
        <form action="/form" method="post" enctype="{enctype}">
            <p>Sample Rate (ms): <span id="sV">{SampleVal}</span> </p>
            <input type="range" min="10" max="500" value="{SampleVal}" id="Sample" name="Sample">
            <p>Minimum Range:<span>{MinValDisp}</span></p>
            <input type="range" min="-255" max="255" value="{MinValDisp}" id="MinVal" name="MinVal">
            <p>Maximum Range:<span>{MaxValDisp}</span></p>
            <input type="range" min="-255" max="255" value="{MaxValDisp}" id="MaxVal" name="MaxVal">
            <p>Minimum Motion Change:<span id="ra">{ChangeVal}</span></p>
            <input type="range" min="1" max="50" value="{ChangeVal}" id="Change" name="Change">
            <p>Set Deadband:<span id="dB">{DeadbandVal}</span></p>
            <input type="range" min="0" max="100" value="{DeadbandVal}" id="Deadband" name="Deadband">
            <p>Motion Options</p>
            <input type="radio" name="Motion" id="RelativeMotion" value="RelativeMotion" checked="checked"> Relative Motion
            <input type="radio" name="Motion" id="ChangeInMotion" value="ChangeInMotion"> Change in Motion<br>
            <br><input type="submit" value="Submit">
        </form>
        {submitted_value}
    </body>
</html>
"""


@server.route("/form", [GET, POST])
def form(request: Request):
    """
    Serve a form with the given enctype, and display back the submitted value.
    """
    global sampling_ms
    global AXIS_MIN # Minimum raw axis value.
    global AXIS_MAX # Maximum raw axis value.
    global AXIS_DB # Deadband Change minimum.
    global minChange
    enctype = request.query_params.get("enctype", "text/plain")

    if request.method == POST:
        sampling_ms = int(request.form_data.get("Sample"))
        AXIS_MIN = int(request.form_data.get("MinVal"))
        AXIS_MAX = int(request.form_data.get("MaxVal"))
        minChange = int(request.form_data.get("Change"))
        AXIS_DB = int(request.form_data.get("Deadband"))
        posted_Motion = request.form_data.get("Motion")

    return Response(
        request,
        FORM_HTML_TEMPLATE.format(
            enctype=enctype,
            submitted_value=(
                "<h3>Updated</h3>"
                # f"<h3>Submitted form Sample: {sampling_ms}ms</h3>\n<h3>Submitted form Range: {minChange}</h3>\n<h3>Submitted form Deadband: {posted_Deadband}</h3>\n<h3>Submitted form motion: {posted_Motion}</h3>"
                if request.method == POST
                else ""
            ),
            MinValDisp=(
                f"{AXIS_MIN}"
                if request.method == POST
                else f"{AXIS_MIN}"
            ),
            MaxValDisp=(
                f"{AXIS_MAX}"
                if request.method == POST
                else f"{AXIS_MAX}"
            ),
            SampleVal=(
                f"{sampling_ms}"
                if request.method == POST
                else f"{sampling_ms}"
            ),
            ChangeVal=(
                f"{minChange}"
                if request.method == POST
                else f"{minChange}"
            ),
            DeadbandVal=(
                f"{AXIS_DB}"
                if request.method == POST
                else f"{AXIS_DB}"
            ),
        ),
        content_type="text/html",
    )


server.start(str(wifi.radio.ipv4_address_ap))

while True:

    try:
        gyro_array = sensor.gyro()
        accel_array = sensor.acceleration()
        DB = AXIS_MIN + (AXIS_MAX - AXIS_MIN)/2
        X = int(accel_array[0]*factor)
        if X > AXIS_MIN and X < AXIS_MAX:
            if X > DB-AXIS_DB and X < DB+AXIS_DB:
                hotas.axis[0].source_value = 125
            # print(f"X: {X}")
            elif X < hotas.axis[0].source_value - minChange or X > hotas.axis[0].source_value + minChange:
                hotas.axis[0].source_value = X
        Y = 0-int(accel_array[1]*factor)
        if Y > AXIS_MIN and Y < AXIS_MAX:
            if Y > DB-AXIS_DB and Y < DB+AXIS_DB:
                hotas.axis[1].source_value = 125
            elif Y < hotas.axis[1].source_value - minChange or Y > hotas.axis[1].source_value + minChange:
                hotas.axis[1].source_value = Y
        if jhat:
            X = jhat.get_x()
            if X > AXIS_MIN/2 and X < AXIS_MAX/2:
                if X > DB/2-AXIS_DB and X < DB/2+AXIS_DB:
                    hotas.axis[2].source_value = 0
                    # print(f"X: {X}")
                elif X < hotas.axis[2].source_value - minChange or X > hotas.axis[2].source_value + minChange:
                    hotas.axis[2].source_value = X
            Y = jhat.get_y()
            if Y > AXIS_MIN/2 and Y < AXIS_MAX/2:
                if Y > DB/2-AXIS_DB and Y < DB/2+AXIS_DB:
                    hotas.axis[3].source_value = 0
                    # print(f"X: {X}")
                elif Y < hotas.axis[3].source_value - minChange or Y > hotas.axis[3].source_value + minChange:
                    hotas.axis[3].source_value = Y
                hotas.button[0].source_value = 1 - jhat.get_button_status()
        hotas.update()
        # print(jhat.get_x())
        # print(accel_array)

                # Process any waiting requests
        pool_result = server.poll()

        if pool_result == REQUEST_HANDLED_RESPONSE_SENT:
            # Do something only after handling a request
            pass

        time.sleep(sampling_ms/1000)

        # If you want you can stop the server by calling server.stop() anywhere in your code
    except OSError as error:
        print(error)
        continue
