import config
"""
LVGL Configuration for JC3248W535EN Display
===========================================

Display: JC3248W535EN with AXS15231B controller
Resolution: 320x480 pixels
Interface: QSPI (4-wire SPI)
Touch: AXS15231 capacitive touch controller

Hardware connections:
- Display: QSPI interface on ESP32-S3
- Touch: I2C interface
"""

from micropython import const
import machine
import lcd_bus
import lvgl as lv

# =============================================================================
# Hardware Initialization
# =============================================================================

# Prevent double-initialization after soft reboot
try:
    _lv_config_initialized
except NameError:
    _lv_config_initialized = True

    # Initialize QSPI bus for display
    import time
    time.sleep(2)

    spi_bus = machine.SPI.Bus(
        host=1,  # SPI2_HOST
        sck=config.SCLK_PIN,
        quad_pins=(config.DATA0_PIN, config.DATA1_PIN, config.DATA2_PIN, config.DATA3_PIN)
    )

    # Create display bus interface
    display_bus = lcd_bus.SPIBus(
        spi_bus=spi_bus,
        dc=config.DC_PIN,
        cs=config.CS_PIN,
        freq=config.FREQ,
        spi_mode=3,      # SPI mode 3 (CPOL=1, CPHA=1)
        quad=True        # Enable QSPI mode (4-wire)
    )

    # Allocate frame buffers in SPIRAM for better performance
    fb1 = display_bus.allocate_framebuffer(config.BUFFER_SIZE, lcd_bus.MEMORY_SPIRAM)
    fb2 = display_bus.allocate_framebuffer(config.BUFFER_SIZE, lcd_bus.MEMORY_SPIRAM)
else:
    # Already initialized, skip hardware init
    pass

# =============================================================================
# Display Driver Setup
# =============================================================================

import axs15231b

display = axs15231b.AXS15231B(
    display_bus,
    config.DISPLAY_WIDTH,
    config.DISPLAY_HEIGHT,
    frame_buffer1=fb1,
    frame_buffer2=fb2,
    backlight_pin=config.BACKLIGHT_PIN,
    color_space=lv.COLOR_FORMAT.RGB565,
    rgb565_byte_swap=True,           # Required for this display
    backlight_on_state=axs15231b.STATE_PWM
)

# Initialize display
print(f"Initializing {config.DISPLAY_WIDTH}x{config.DISPLAY_HEIGHT} QSPI display...")
display.set_power(True)
display.set_backlight(80)  # 80% brightness
display.init()
print("Display initialized successfully!")

# =============================================================================
# Touch Controller Setup
# =============================================================================

class TouchCal:
    """Touch calibration data placeholder"""
    def __init__(self):
        # Calibration parameters (not needed for this touch controller)
        self.alphaX = None
        self.betaX = None
        self.deltaX = None
        self.alphaY = None
        self.betaY = None
        self.deltaY = None
        self.mirrorX = False
        self.mirrorY = False

    @staticmethod
    def save():
        """Save calibration data (placeholder)"""
        pass

# Initialize I2C bus for touch controller
import axs15231
from i2c import I2C

i2c_bus = I2C.Bus(host=1, sda=config.TOUCH_SDA_PIN, scl=config.TOUCH_SCL_PIN)
touch_i2c = I2C.Device(i2c_bus, axs15231.I2C_ADDR, axs15231.BITS)

# Create touch input device
cal = TouchCal()
touch = axs15231.AXS15231(touch_i2c, touch_cal=cal, debug=False)

# Initialize touch controller
indev = axs15231.AXS15231(touch_i2c, debug=False)
indev.enable_input_priority()

print(f"Touch controller calibrated: {indev.is_calibrated}")
print("System ready!")

# =============================================================================
# Usage Notes
# =============================================================================
"""
After importing this module, you can use:

- display: AXS15231B display driver instance
- touch: AXS15231 touch controller instance  
- WIDTH, HEIGHT: Display dimensions

Example:
    import lv_config

    # Display is automatically initialized
    # Create LVGL objects and use normally

    label = lv.label(lv.screen_active())
    label.set_text("Hello World!")
    label.center()
"""
