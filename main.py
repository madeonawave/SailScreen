import machine
import config
import time
import lv_config
import lvgl as lv
from display import DisplayUI
from espnow_manager import ESPNowMessenger
from microGPS import MicropyGPS

time.sleep(2)  # Give time for USB/REPL to settle

# Initialize GPS parser and UART
gps = MicropyGPS()
uart = machine.UART(config.GPS_UART_ID,
                    baudrate=config.GPS_BAUDRATE,
                    tx=config.GPS_TX_PIN,
                    rx=config.GPS_RX_PIN)

ui = DisplayUI()
messenger = ESPNowMessenger()

# Load peers from file and add to messenger
import re

def is_valid_mac(mac):
    # MAC address should be 6 pairs of hex digits separated by ':'
    # Example: AA:BB:CC:DD:EE:FF
    return bool(re.match(r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$", mac))

def load_peers():
    try:
        with open("/peers.txt") as f:
            macs = [line.strip() for line in f if line.strip()]
            return [mac for mac in macs if is_valid_mac(mac)]
    except OSError:
        return []

for mac_str in load_peers():
    try:
        peer_mac = ESPNowMessenger.mac_str_to_bytes(mac_str)
        messenger.add_peer(peer_mac)
    except Exception as e:
        print("Invalid MAC:", mac_str, e)

last_update = 0

try:
    while True:
        # 1. Read all available bytes from UART and feed to GPS parser
        while uart.any():
            b = uart.read(1)
            if b:
                gps.update(chr(b[0]))

        # 2. Always update the display with the latest GPS data
        try:
            # Speed in knots (float, 0th element of gps.speed)
            speed_knots = gps.speed[0]
            course_val = float(gps.course)
            compass = "{:.0f}°".format(course_val)
            # Update display
            ui.set_display_text("{:.1f}".format(speed_knots))
            ui.set_compass_text(str(compass))
            # Add speed to chart
            ui.update_chart(int(speed_knots * 10))
            # If on GPS screen, update lat/lon and Sat/Fix
            lv.task_handler()
            if ui.active_screen == 1:
                try:
                    lat = gps.latitude[0] + gps.latitude[1]/60 if gps.latitude else None
                    if gps.latitude[2] == 'S':
                        lat = -lat
                    lon = gps.longitude[0] + gps.longitude[1]/60 if gps.longitude else None
                    if gps.longitude[2] == 'W':
                        lon = -lon
                    ui.show_gps_screen(
                        lat, lon,
                        satellites_in_use=getattr(gps, "satellites_in_use", None),
                        fix_stat=getattr(gps, "fix_stat", None)
                    )
                except Exception:
                    ui.show_gps_screen(None, None, None, None)


        except ValueError:
            # Optionally show waiting message
            ui.set_display_text("...")
            ui.set_compass_text("...")

        # 3. Send speed and compass to all peers every
        now = time.ticks_ms()
        try:
            for mac_str in load_peers():
                peer_mac = ESPNowMessenger.mac_str_to_bytes(mac_str)
                messenger.send_to(peer_mac, "speedometer/speed", "{:.1f}".format(gps.speed[0]))
                messenger.send_to(peer_mac, "speedometer/compass", str(gps.compass_direction()))
        except OSError as e:
            if getattr(e, 'errno', None) == 116:
                print("ESP-NOW send timeout (ETIMEDOUT)")
            else:
                print("ESP-NOW send error:", e)
        last_update = now

        lv.tick_inc(10)
        lv.task_handler()
        time.sleep_ms(10)

except Exception as e:
    print("Exception in main loop:", e)
