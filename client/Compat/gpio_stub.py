# Minimal stub for RPi.GPIO to allow running in VM/Desktop without hardware
# Provides the subset used in the project: setmode, setup, output, input, cleanup, constants

BCM = 11
BOARD = 10
IN = 0
OUT = 1
PUD_UP = 2
PUD_DOWN = 3
HIGH = 1
LOW = 0

_state = {}


def setmode(mode):
    return None


def setup(channel, direction, pull_up_down=None):
    _state[channel] = LOW


def output(channel, value):
    _state[channel] = HIGH if value else LOW


def input(channel):
    return _state.get(channel, LOW)


def cleanup(channel=None):
    if channel is None:
        _state.clear()
    else:
        _state.pop(channel, None)
