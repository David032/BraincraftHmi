from email.mime import audio
import json
import os
import adafruit_imageload
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
from adafruit_httpserver import Request, Response, Server, GET, POST, Status, BAD_REQUEST_400, as_route
from digitalio import DigitalInOut, Direction, Pull
import pyaudio
import wave

settings = {}
# load settings from settings.json
with open("settings.json", "r") as f:
    settings = json.load(f)

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

button = DigitalInOut(board.D17)
button.direction = Direction.INPUT
button.pull = Pull.UP

directory_root = os.path.dirname(os.path.abspath(__file__))

# Create the audio directory if it doesn't exist
if not os.path.exists(f"{directory_root}/audio"):
    os.makedirs(f"{directory_root}/audio")

print(f"Directory root: {directory_root}")
# for each element in the assets folder, create a group and add it to the screen group
class DisplayElement:
    def __init__(self, name: str, group: displayio.Group):
        self.name = name
        self.group = group

    def show(self):
        self.group.hidden = False
display_elements: list[DisplayElement] = []
def load_display_elements():
    global display_elements
    for filename in os.listdir(f"{directory_root}/assets"):
        print(f"Found file: {filename}")
        if filename.endswith(".bmp"):
            element_name = filename[:-4]  # remove the .bmp extension
            print(f"Loading element: {element_name} from file: {filename}")
            scale_factor = 6
            element_group = displayio.Group(scale=scale_factor, x= (-1 * (scale_factor*32)) + 20, y=-1 * (scale_factor*38))
            screen.append(element_group)
            # load the image and add it to the group
            bitmap, pallette = adafruit_imageload.load(f"{directory_root}/assets/{filename}",bitmap=displayio.Bitmap, palette=displayio.Palette)
            image_sprite = displayio.TileGrid(bitmap, pixel_shader=pallette, x=32, y=38) # type: ignore

            element_group.append(image_sprite)
            element = DisplayElement(element_name, element_group)
            print(f"Adding element: {element_name} to display_elements list")
            display_elements.append(element)
            # hide the group by default
            element_group.hidden = True
load_display_elements()

pool = socket
server = Server(pool, "/static", debug=True)  # type: ignore

def interrupt(*args, **kwargs):
    for i in range(3):
        leds[i] = (0, 0, 0)
        leds.brightness = 0.0
        leds.show()
    time.sleep(0.5)
    clear_display()
    sys.exit(0)

def random_color():
    return random.randrange(0, 7) * 32


@server.route("/leds", [GET, POST])
def leds_route(request: Request):
    if request.method == GET:
        leds_state = [(leds[0], leds[1], leds[2])]
        return Response(request, f"LEDs route GET request received. LED states: {leds_state}")
    elif request.method == POST:
        json_data = json.loads(request.body.decode("utf-8"))
        print(f"Received POST data: {json_data}")
        for i in range(3):
            r, g, b, w = get_led_values(json_data, i)
            print(f"Setting LED {i} to color: {r}, {g}, {b}, {w}")
            leds[i] = (r, g, b, w)
        leds.brightness = float(json_data['brightness'])
        leds.show()
        return Response(request, f"LEDs route POST request received with data: {json_data}")

def get_led_values(json_data, i):
    r = int(json_data['colour'][str(i)]["r"])
    g = int(json_data['colour'][str(i)]["g"])
    b = int(json_data['colour'][str(i)]["b"])
    w = int(json_data['colour'][str(i)]["w"])
    return r,g,b,w

@server.route("/leds/<led_id>", [GET, POST])
def leds_id_route(request: Request, led_id: int):
    if led_id < 0 or led_id >= 3:
        return Response(request, f"Invalid LED ID: {led_id}. Must be between 0 and 2.", status=BAD_REQUEST_400)

    if request.method == GET:
        return Response(request, f"LED {led_id} route GET request received. Current color: {leds[led_id]}")
    elif request.method == POST:
        json_data = json.loads(request.body.decode("utf-8"))
        print(f"Received POST data: {json_data}")
        r, g, b, w = get_led_values(json_data, led_id)
        print(f"Setting LED {led_id} to color: {r}, {g}, {b}, {w}")
        leds[led_id] = (r, g, b, w)
        leds.brightness = float(json_data['brightness'])
        leds.show()
        return Response(request, f"LED {led_id} route POST request received with data: {json_data}")

@server.route("/display", [GET, POST])
def display_route(request: Request):
    if request.method == GET:
        return Response(request, "Display route GET request received.")
    elif request.method == POST:
        json_data = json.loads(request.body.decode("utf-8"))
        print(f"Received POST data: {json_data}")
        return Response(request, f"Display route POST request received with data: {json_data}")

def clear_display():
    for element in display_elements:
        element.group.hidden = True
    display.refresh()

@server.route("/display/<element>", [POST])
def display_element_route(request: Request, element: str):
    if request.method == POST:
        clear_display()
        match element.lower():
            case "alert":
                print(f"Showing alert element")
                elementToShow = [e for i, e in enumerate(display_elements) if e.name == "emote_anger"][0]
                elementToShow.show()
                display.refresh()
            case "info":
                print(f"Showing info element")
                elementToShow = [e for i, e in enumerate(display_elements) if e.name == "emote_idea"][0]
                elementToShow.show()
                display.refresh()
            case "warning":
                print(f"Showing warning element")
                elementToShow = [e for i, e in enumerate(display_elements) if e.name == "emote_exclamations"][0]
                elementToShow.show()
                display.refresh()
            case "error":
                print(f"Showing error element")
                elementToShow = [e for i, e in enumerate(display_elements) if e.name == "emote_exclamation"][0]
                elementToShow.show()
                display.refresh()
            case "message":
                print(f"Showing message element")
                elementToShow = [e for i, e in enumerate(display_elements) if e.name == "emote_circle"][0]
                elementToShow.show()
                display.refresh()
            case _:
                print(f"Unknown element: {element}")

        return Response(request, f"Display element route POST request received with data")

@server.route("/shutdown", [POST])
def shutdown_route(request: Request):
    print("Shutdown route POST request received. Shutting down the server.")
    leds.fill((0, 0, 0))
    leds.brightness = 0.0
    leds.show()
    clear_display()
    server.stop()

@server.route("/audio_input", [POST])
def audio_input_route(request: Request):
    if request.method == POST:
        #Get the audio file from the request
        audio_file = request.file.get("file")
        if audio_file:
            return Response(request, f"Audio input route POST request received with file: {audio_file.filename}")
        

def record_audio(duration=30):
    # Initialize PyAudio
    p = pyaudio.PyAudio()

    BITRATE = 44100
    CHANNELS = 1
    BITRATE = 44100
    CHUNK_SIZE = 512
    FORMAT = pyaudio.paInt16

    # Open a stream
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=BITRATE,
                    input=True,
                    input_device_index=settings.get("Audio_Input_Device"),
                    frames_per_buffer=CHUNK_SIZE)

    # Start the stream
    stream.start_stream()

    # Show the recording indicator on the display
    clear_display()
    elementToShow = [e for i, e in enumerate(display_elements) if e.name == "emote_redcircle"][0]
    elementToShow.show()
    display.refresh()

    # Record audio data
    audio_data = []
    for i in range(0, int(BITRATE / CHUNK_SIZE * duration)):
        data = stream.read(CHUNK_SIZE)
        audio_data.append(data)

    # Stop the stream
    stream.stop_stream()
    stream.close()

    # Cleanup PyAudio
    p.terminate()

    # Get the current timestamp for the filename
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"{directory_root}/audio/{timestamp}.wav"
    
    waveFile = wave.open(filename, 'wb')
    waveFile.setnchannels(1)
    waveFile.setsampwidth(p.get_sample_size(FORMAT))
    waveFile.setframerate(BITRATE)
    waveFile.writeframes(b''.join(audio_data))
    waveFile.close()

    clear_display() 
    display.refresh() 
    # Return the audio data
    return filename


if __name__ == "__main__":
    signal.signal(signal.SIGINT, interrupt)
    load_display_elements()

    #TODO: Wrap this in a check since it should only be needed once
    print("-----Audio Checks-----")
    audio = pyaudio.PyAudio()
    info = audio.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')
    for i in range(0, numdevices): # type: ignore
        if (audio.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0: # type: ignore
            print("Input Device id ", i, " - ", audio.get_device_info_by_host_api_device_index(0, i).get('name'))
    audio.terminate()
    print("----------------------")



    server.start()

    while True:
        pool_result = server.poll()
        if button.value == False:  # Button is pressed
            print("Button pressed. Recording audio...")
            # Record 30 seconds of audio
            recording = record_audio(duration=30)
            if settings.get("Audio_Destination") == "url":
                # send the audio file to the server
                import requests
                url = settings.get("Audio_Destination_URL")
                files = {'file': open(recording, 'rb')}
                response = requests.post(url, files=files)
                print(f"Server response: {response.status_code} - {response.text}")
        time.sleep(0.5)