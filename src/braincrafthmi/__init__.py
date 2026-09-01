import json

import board
import adafruit_dotstar as dotstar
import random 
import time
from adafruit_st7789 import ST7789
import displayio
import fourwire
from adafruit_display_shapes.rect import Rect
from adafruit_display_shapes.circle import Circle
from adafruit_display_shapes.roundrect import RoundRect
from adafruit_display_shapes.triangle import Triangle
import terminalio
from adafruit_display_text import label
import signal
import sys
import socket
from adafruit_httpserver import Request, Response, Server, GET, POST

# Initialize DotStar LEDs
leds = dotstar.DotStar(board.D6, board.D5, 3, brightness=0.2)
leds.fill((255, 255, 0))

# Init display
displayio.release_displays()
spi = board.SPI()
tft_cs = board.CE0
tft_dc = board.D25
tft_lite = board.D26

display_bus = fourwire.FourWire(spi, command=tft_dc)

display = ST7789(
    display_bus,
    width=240,
    height=240,
    rowstart=80,
    rotation=180,
    backlight_pin=tft_lite,
)
screen = displayio.Group()
display.root_group = screen

rect = Rect(0, 0, 80, 40, fill=0x00FF00)
circle = Circle(100, 100, 20, fill=0x00FF00, outline=0xFF00FF)
triangle = Triangle(170, 50, 120, 140, 210, 160, fill=0x00FF00, outline=0xFF00FF)
roundrect = RoundRect(50, 100, 40, 80, 10, fill=0x0, outline=0xFF00FF, stroke=3)
my_label = label.Label(terminalio.FONT, text="My Label Text", color=(255,255,255), scale=2)
my_label.x = 50
my_label.y = 200
screen.append(rect)
screen.append(circle)
screen.append(triangle)
screen.append(roundrect)
screen.append(my_label)

pool = socket
server = Server(pool, "/static", debug=True)

def interrupt(*args, **kwargs):
    for i in range(3):
        leds[i] = (0, 0, 0)
        leds.brightness = 0.0
        leds.show()
    time.sleep(0.5)
    sys.exit(0)

def main() -> None:
    print("Hello from braincrafthmi!")

def random_color():
    return random.randrange(0, 7) * 32

signal.signal(signal.SIGINT, interrupt)

@server.route("/")
def base(request: Request):
    """
    Serve a default static plain text message.
    """
    return Response(request, "Hello from the CircuitPython HTTP Server!")


@server.route("/leds", [GET, POST])
def leds_route(request: Request):
    if request.method == GET:
        leds_state = [(leds[0], leds[1], leds[2])]
        return Response(request, f"LEDs route GET request received. LED states: {leds_state}")
    elif request.method == POST:
        json_data = json.loads(request.body.decode("utf-8"))
        print(f"Received POST data: {json_data}")
        for i in range(3):
            r = int(json_data['colour'][str(i)]["r"])
            g = int(json_data['colour'][str(i)]["g"])
            b = int(json_data['colour'][str(i)]["b"])
            w = int(json_data['colour'][str(i)]["w"])
            print(f"Setting LED {i} to color: {r}, {g}, {b}, {w}")
            leds[i] = (r, g, b, w)
        leds.brightness = float(json_data['brightness'])
        leds.show()
        return Response(request, f"LEDs route POST request received with data: {json_data}")

@server.route("/display", [GET, POST])
def display_route(request: Request):
    if request.method == GET:
        return Response(request, "Display route GET request received.")
    elif request.method == POST:
        json_data = json.loads(request.body.decode("utf-8"))
        print(f"Received POST data: {json_data}")
        return Response(request, f"Display route POST request received with data: {json_data}")

@server.route("/shutdown", [POST])
def shutdown_route(request: Request):
    print("Shutdown route POST request received. Shutting down the server.")
    leds.fill((0, 0, 0))
    leds.brightness = 0.0
    leds.show()
    server.stop()


server.start()

while True:
    pool_result = server.poll()
    #TODO: Check if button is being held
    #TODO: check for joystick input. Not sure what to do with it. 
    time.sleep(0.5)