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
uart = machine.UART(
    config.GPS_UART_ID,
    baudrate=config.GPS_BAUDRATE,
    tx=config.GPS_TX_PIN,
    rx=config.GPS_RX_PIN,
)

# =============================================================================
# GPS diagnostics (temporary) - logs what the receiver actually reports
# =============================================================================
_gps_log_path = "/gps_log.txt"
_gps_diag = {
    "bytes": 0,
    "sentences": 0,
    "cksum_err": 0,
    "unknown": 0,
    "gsv": 0,
    "fix": "?",
    "last": "",
}
_gps_line = b""
_last_gps_log = time.ticks_ms()


def _nmea_cksum_ok(line):
    line = line.rstrip()
    if b"*" not in line:
        return True
    hdr, _, cks = line.partition(b"*")
    cks = cks[:2]
    c = 0
    for ch in hdr[1:]:
        c ^= ch
    return ("%02X" % c).encode() == cks


def _on_nmea(line):
    d = _gps_diag
    d["sentences"] += 1
    try:
        line_txt = line.decode("utf-8").strip()
    except Exception:
        line_txt = ""
    if not _nmea_cksum_ok(line):
        d["cksum_err"] += 1
    if line.startswith(b"$GPGSV"):
        parts = line_txt.split(",")
        if len(parts) > 3:
            try:
                d["gsv"] = int(parts[3])
            except ValueError:
                pass
    elif line.startswith(b"$GPRMC"):
        parts = line_txt.split(",")
        if len(parts) > 2:
            d["fix"] = parts[2]  # 'A' = active fix, 'V' = void
    if not (
        line.startswith(b"$GP")
        or line.startswith(b"$GL")
        or line.startswith(b"$GA")
        or line.startswith(b"$BD")
    ):
        d["unknown"] += 1
    d["last"] = line_txt


def _log_gps_status():
    d = _gps_diag
    line = (
        "gps: bytes=%d sentences=%d cksum_err=%d unknown=%d gsv_sats=%d fix=%.6s last=%s"
        % (
            d["bytes"],
            d["sentences"],
            d["cksum_err"],
            d["unknown"],
            d["gsv"],
            d["fix"],
            d["last"],
        )
    )
    print("[GPS]", line)
    try:
        import os

        try:
            with open(_gps_log_path, "r") as f:
                existing = f.read().count("\n")
        except OSError:
            existing = 0
        if existing > 150:
            try:
                os.remove(_gps_log_path)
            except OSError:
                pass
        with open(_gps_log_path, "a") as f:
            f.write(line + "\n")
    except OSError as e:
        print("[GPS] log write failed:", e)


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
last_valid_speed = 0.0

try:
    while True:
        # 1. Read all available bytes from UART and feed to GPS parser
        while uart.any():
            b = uart.read(1)
            if b:
                gps.update(chr(b[0]))
                _gps_diag["bytes"] += 1
                _gps_line += b
                if b == b"\n":
                    _on_nmea(_gps_line)
                    _gps_line = b""

        # Periodic GPS diagnostics log
        if time.ticks_ms() - _last_gps_log >= 15000:
            _last_gps_log = time.ticks_ms()
            _log_gps_status()

        # 2. Update display with GPS data (only when valid, otherwise keep previous)
        if gps.valid:
            last_valid_speed = gps.speed[0]
            speed_knots = last_valid_speed
            course_val = float(gps.course)
            # Pad to 3 digits so the degree symbol stays in a fixed column
            compass = "{}°".format("{:>3}".format(int(round(course_val)) % 360))
            ui.set_display_text("{:.1f}".format(speed_knots))
            ui.set_compass_text(str(compass))
            ui.update_chart(int(speed_knots * 10))
            lv.task_handler()
            if ui.active_screen == 1:
                try:
                    lat = (
                        gps.latitude[0] + gps.latitude[1] / 60 if gps.latitude else None
                    )
                    if gps.latitude[2] == "S":
                        lat = -lat
                    lon = (
                        gps.longitude[0] + gps.longitude[1] / 60
                        if gps.longitude
                        else None
                    )
                    if gps.longitude[2] == "W":
                        lon = -lon
                    ui.show_gps_screen(
                        lat,
                        lon,
                        satellites_in_use=getattr(gps, "satellites_in_use", None),
                        fix_stat=getattr(gps, "fix_stat", None),
                    )
                except Exception:
                    ui.show_gps_screen(None, None, None, None)
        else:
            ui.set_display_text("{:.1f}".format(last_valid_speed))

        # 3. Send speed and compass to all peers every
        now = time.ticks_ms()
        try:
            for mac_str in load_peers():
                peer_mac = ESPNowMessenger.mac_str_to_bytes(mac_str)
                messenger.send_to(
                    peer_mac, "speedometer/speed", "{:.1f}".format(gps.speed[0])
                )
                messenger.send_to(
                    peer_mac, "speedometer/compass", str(gps.compass_direction())
                )
        except OSError as e:
            if getattr(e, "errno", None) == 116:
                print("ESP-NOW send timeout (ETIMEDOUT)")
            else:
                print("ESP-NOW send error:", e)
        last_update = now

        lv.tick_inc(10)
        lv.task_handler()
        time.sleep_ms(10)

except Exception as e:
    print("Exception in main loop:", e)
