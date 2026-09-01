import json
import re
from pathlib import Path
from types import SimpleNamespace


MODULE_PATH = Path(__file__).resolve().parents[1] / "src" / "braincrafthmi" / "__init__.py"


class FakeResponse:
    def __init__(self, request, body):
        self.request = request
        self.body = body


class FakeLEDs:
    def __init__(self, values=((0, 0, 0), (0, 0, 0), (0, 0, 0)), brightness=1.0):
        self._values = [tuple(value) for value in values]
        self.brightness = brightness
        self.show_calls = 0

    def __getitem__(self, index):
        return self._values[index]

    def __setitem__(self, index, value):
        self._values[index] = tuple(value)

    def fill(self, value):
        self._values = [tuple(value) for _ in range(3)]

    def show(self):
        self.show_calls += 1


def _load_leds_route():
    source = MODULE_PATH.read_text()
    pattern = r"def leds_route\(request: Request\):\n(?:    .*\n)*?(?=\n@server\.route\(|\n\ndef |\Z)"
    match = re.search(pattern, source)
    if not match:
        raise AssertionError("Could not find leds_route in source")

    namespace = {
        "json": json,
        "Request": type("Request", (), {}),
        "GET": "GET",
        "POST": "POST",
        "Response": FakeResponse,
        "leds": FakeLEDs(values=((255, 0, 0), (0, 255, 0), (0, 0, 255)), brightness=0.5),
    }
    exec(match.group(0), namespace)
    return namespace["leds_route"], namespace["leds"]


def test_leds_route_get():
    leds_route, leds = _load_leds_route()
    request = SimpleNamespace(method="GET", body=b"")
    response = leds_route(request)

    assert "LEDs route GET request received" in response.body
    assert "LED states" in response.body
    assert "(255, 0, 0)" in response.body
    assert "(0, 255, 0)" in response.body
    assert "(0, 0, 255)" in response.body
    assert leds.brightness == 0.5


def test_leds_route_post_updates_each_led_and_brightness():
    leds_route, leds = _load_leds_route()

    payload = {
        "brightness": 0.5,
        "colour": {
            "0": {"r": 255, "g": 0, "b": 0, "w": 1},
            "1": {"r": 0, "g": 255, "b": 0, "w": 1},
            "2": {"r": 0, "g": 0, "b": 255, "w": 1},
        },
    }

    request = SimpleNamespace(method="POST", body=json.dumps(payload).encode("utf-8"))
    response = leds_route(request)

    assert "LEDs route POST request received" in response.body
    assert leds[0] == (255, 0, 0, 1)
    assert leds[1] == (0, 255, 0, 1)
    assert leds[2] == (0, 0, 255, 1)
    assert leds.brightness == 0.5
    assert leds.show_calls == 1