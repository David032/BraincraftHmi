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

# Initialize DotStar LEDs
leds = dotstar.DotStar(board.D6, board.D5, 3, brightness=0.2)
leds.fill((0, 255, 0))

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
my_label = label.Label(terminalio.FONT, text="My Label Text", color=(255,0,0))
screen.append(rect)
screen.append(circle)
screen.append(triangle)
screen.append(roundrect)
screen.append(my_label)



def main() -> None:
    print("Hello from braincrafthmi!")

def random_color():
    return random.randrange(0, 7) * 32

while True:
    for i in range(3):
        leds[i] = (random_color(), random_color(), random_color())
    leds.show()
    time.sleep(0.5)
