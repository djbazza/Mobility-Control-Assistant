# SPDX-FileCopyrightText: 2024 Michał Pokusa
#
# SPDX-License-Identifier: Unlicense

import socketpool
import wifi

from adafruit_httpserver import Server, Route, as_route, Request, Response, GET, POST

AP_SSID = "MC"
AP_PASSWORD = "helpmemove"

print("Creating access point...")
wifi.radio.start_ap(ssid=AP_SSID, password=AP_PASSWORD)
print(f"Created access point {AP_SSID}")

pool = socketpool.SocketPool(wifi.radio)
server = Server(pool, "/static", debug=True)

InitSample = 100
InitRange = 125
InitDeadband = 125

FORM_HTML_TEMPLATE = """
<html lang="en">
    <head>
        <title>Form with {enctype} enctype</title>
    </head>
    <body>
        <a href="/form?enctype=application/x-www-form-urlencoded">
            <button>Load <strong>application/x-www-form-urlencoded</strong> form</button>
        </a><br />
        <a href="/form?enctype=multipart/form-data">
            <button>Load <strong>multipart/form-data</strong> form</button>
        </a><br />
        <a href="/form?enctype=text/plain">
            <button>Load <strong>text/plain</strong> form</button>
        </a><br />

        <h2>Form with {enctype} enctype</h2>
        <form action="/form" method="post" enctype="{enctype}">
            <p>Sample Rate (ms): <span id="sV">{SampleVal}</span> </p>
            <input type="range" min="10" max="500" value="{SampleVal}" id="Sample" name="Sample">
            <p>Motion Range:<span id="ra">{RangeVal}</span></p>
            <input type="range" min="1" max="255" value="{RangeVal}" id="Range" name="Range">
            <p>Set Deadband:<span id="dB">{DeadbandVal}</span></p>
            <input type="range" min="1" max="255" value="{DeadbandVal}" id="Deadband" name="Deadband">
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
    enctype = request.query_params.get("enctype", "text/plain")

    if request.method == POST:
        posted_Sample = request.form_data.get("Sample")
        posted_Range = request.form_data.get("Range")
        posted_Deadband = request.form_data.get("Deadband")
        posted_Motion = request.form_data.get("Motion")

    return Response(
        request,
        FORM_HTML_TEMPLATE.format(
            enctype=enctype,
            submitted_value=(
                f"<h3>Enctype: {enctype}</h3>\n<h3>Submitted form Sample: {posted_Sample}ms</h3>\n<h3>Submitted form Range: {posted_Range}</h3>\n<h3>Submitted form Deadband: {posted_Deadband}</h3>\n<h3>Submitted form motion: {posted_Motion}</h3>"
                if request.method == POST
                else ""
            ),
            SampleVal=(
                f"{posted_Sample}"
                if request.method == POST
                else f"{InitSample}"
            ),
            RangeVal=(
                f"{posted_Range}"
                if request.method == POST
                else f"{InitRange}"
            ),
            DeadbandVal=(
                f"{posted_Deadband}"
                if request.method == POST
                else f"{InitDeadband}"
            ),
        ),
        content_type="text/html",
    )


server.serve_forever(str(wifi.radio.ipv4_address_ap))
