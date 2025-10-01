# Centralized configuration for pins, UART, and GPS

from micropython import const

# Display pins
DISPLAY_WIDTH = const(320)
DISPLAY_HEIGHT = const(480)
SCLK_PIN = const(47)
DATA0_PIN = const(21)
DATA1_PIN = const(48)
DATA2_PIN = const(40)
DATA3_PIN = const(39)
CS_PIN = const(45)
DC_PIN = const(8)
BACKLIGHT_PIN = const(1)
RESET_PIN = None

# Display timing
FREQ = 40000000  # 40 MHz QSPI frequency

# I2C Touch Pins (AXS15231 capacitive touch)
TOUCH_SDA_PIN = const(4)    # I2C Data
TOUCH_SCL_PIN = const(8)    # I2C Clock

# GPS UART config
GPS_UART_ID = 2
GPS_TX_PIN = const(17)  # Example, set to your wiring
GPS_RX_PIN = const(18)  # Example, set to your wiring
GPS_BAUDRATE = 9600

BUFFER_SIZE = DISPLAY_WIDTH * DISPLAY_HEIGHT * 2  # RGB565 = 2 bytes per pixel