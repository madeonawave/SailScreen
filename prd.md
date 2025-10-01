# Product Requirements Document

## Device
- **Model:** JC3248W535 (ESP32-S3, 3.5" capacitive touch IPS, 8M PSRAM, 16M flash, 320x480)
- **Display:** axs15231b (QSPI)
- **Touch:** axs15231b (I2C)
- **MicroPython compatible**
- **microSD card**: Used for logging GPS data and storing files.


## Connectivity
- **GPS:** NEO6Mv2
- **Wireless:** ESPNow

## Features

- Parse GPS data and display on screen.
- **Screen 1 (Main):**
  - Speed (knots)
  - Direction (compass)
  - Chart (average speed indicator)
  - Average speed (small text above chart)
- **Screen 2 (GPS Info):**
  - Latitude / Longitude (as floats)
  - Satellite count and GPS fix status (2D/3D/No Fix)
  - Navigation buttons (previous/next)
- **Screen 3 (ESP-NOW Peer Management):**
  - Form to add/remove ESP-NOW peer MAC addresses (no webserver needed)
  - MAC addresses are stored in `/peers.txt` on the device
  - Navigation buttons (previous/next)
- **ESP-NOW:**
  - Device sends speed and compass data to all peers listed in `/peers.txt`
  - Peers can be managed directly from the device UI (screen 3)
- **microSD card:**
  - Used for logging GPS data and storing files (future feature)
- **Touchscreen navigation:**
  - All screens have previous/next navigation buttons
- **No webserver required for configuration**  

# Project Structure and Organization

## 1. Core Directories and Files

- **/display/**
  - `main.py` or `main2.py`  
    *Entry point. Handles app logic, UI, and orchestrates modules.*
  - `lv_config.py`  
    *Display and touch configuration (pins, buses, LVGL setup).*
  - `display.py`  
    *High-level display logic (drawing speed, compass, etc).*
  - `microGPS.py`  
    *GPS NMEA parsing (MicropyGPS).*
  - `espnow_manager.py`  
    *ESPNow connection, send/receive logic.*
  - `config.py`  
    *Centralized configuration: pins, device settings, GPS parameters, etc.*

## 2. Drivers

- `axs15231b.py`, `nv3041aG.py`, `_axs15231b_init.py`, `axs15231.py`  
  *Display and touch drivers. Keep these separate for clarity and reusability.*

## 3. Example Structure

```plaintext
display/
│
├── main.py                # Main application logic
├── [lv_config.py                        # Display/touch config and initialization
├── [display.py]                         # High-level display logic (UI, drawing)
├── [microGPS.py]                        # GPS NMEA parser
├── espnow_manager.py                    # ESPNow communication logic
├── config.py                            # All pin/device config in one place
│
├── [axs15231b.py]                       # Display driver
├── [axs15231.py]                        # Touch driver
├── [nv3041aG.py]                        # (Other display driver)
├── [_axs15231b_init.py]                 # Display init sequence
│
├── [test.py]                            # LVGL test/demo code
├── [prd.md]                             # Product Requirements Document
└── ...


