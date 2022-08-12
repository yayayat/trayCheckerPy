#                 DSUB
#    (12V)  (12V)       (GND) (GND)
#    ╭─────────────────────────────╮
#     \ 5     4     3     2     1 /
#      \   9     8     7     6   /
#       ╰───────────────────────╯
#        (IN1) (IN0) (OUT1)(OUT0)
#    GPIO: 17    27    5     6
#    Wpi:  0     2     21    22

import RPi.GPIO as GPIO
from smbus2 import SMBus
lp5012 = None

CONTROLLER_I2C_ADDRESS = 0x14
OUT_PINS = (6, 5)
IN_PINS = (27, 17)
RED_LEDS = (0x15, 0x12, 0x0E, 0x0C)
GREEN_LEDS = (0x14, 0x11, 0x0F)


def initialize():
    global lp5012
    lp5012 = SMBus(1)
    lp5012.write_byte_data(CONTROLLER_I2C_ADDRESS, 0x17, 0xFF)
    lp5012.write_byte_data(CONTROLLER_I2C_ADDRESS, 0x00, 0b01000000)
    GPIO.setmode(GPIO.BCM)
    for pin in IN_PINS:
        GPIO.setup(pin, GPIO.IN)
    for pin in OUT_PINS:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)
    for LED in RED_LEDS + GREEN_LEDS:
        lp5012.write_byte_data(CONTROLLER_I2C_ADDRESS, LED, 0x0)


def write(respond):
    GPIO.output(OUT_PINS[0], respond & 0x1)
    GPIO.output(OUT_PINS[1], respond & 0x2)


def read():
    request = GPIO.input(IN_PINS[0])
    request += (GPIO.input(IN_PINS[1]) << 1)
    request ^= 0x3
    return request
