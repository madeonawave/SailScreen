import lvgl as lv


class DisplayUI:
    def __init__(self):
        self.gps_next_btn = None
        self.gps_prev_btn = None
        self.lon_label = None
        self.lat_label = None
        self.scrn = lv.screen_active()
        self.scrn.clean()
        self.scrn.set_style_bg_color(lv.color_hex(0x000000), 0)
        self.scrn.set_style_text_font(lv.font_montserrat_24, 0)
        self.third_scrn = None

        # --- Add Previous and Next buttons ---
        self.prev_btn = lv.button(self.scrn)
        self.prev_btn.set_size(40, 40)
        self.prev_btn.align(lv.ALIGN.BOTTOM_LEFT, 10, -10)
        self.prev_btn.set_style_bg_color(lv.color_hex(0x111111), 0)
        self.prev_btn.set_style_bg_opa(lv.OPA.COVER, 0)
        prev_label = lv.label(self.prev_btn)
        prev_label.set_text(lv.SYMBOL.LEFT)

        self.next_btn = lv.button(self.scrn)
        self.next_btn.set_size(40, 40)
        self.next_btn.align(lv.ALIGN.BOTTOM_RIGHT, -10, -10)
        self.next_btn.set_style_bg_color(lv.color_hex(0x111111), 0)
        self.next_btn.set_style_bg_opa(lv.OPA.COVER, 0)
        next_label = lv.label(self.next_btn)
        next_label.set_text(lv.SYMBOL.RIGHT)

        self.d_label = lv.label(self.scrn)
        self.d_label.set_text("--")
        self.d_label.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
        self.d_label.set_style_text_font(lv.font_montserrat_48, 0)
        self.d_label.set_style_text_align(lv.TEXT_ALIGN.CENTER, 0)
        self.d_label.set_style_transform_width(120, 0)
        self.d_label.set_style_transform_height(48, 0)
        self.d_label.set_style_transform_scale(600, 0)
        self.d_label.align(lv.ALIGN.CENTER, -60, -180)  # Move a bit left of center

        self.compass_label = lv.label(self.scrn)
        self.compass_label.set_text("--")
        self.compass_label.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
        self.compass_label.set_style_text_font(lv.font_montserrat_48, 0)
        self.compass_label.set_style_text_align(lv.TEXT_ALIGN.CENTER, 0)
        self.compass_label.align(lv.ALIGN.CENTER, 100, 100)  # Move a bit right of center

        # --- Add a simple chart for speed history ---
        self.chart = lv.chart(self.scrn)
        self.chart.set_size(300, 80)
        self.chart.align(lv.ALIGN.BOTTOM_MID, 0, -10)
        self.chart.set_type(lv.chart.TYPE.LINE)
        self.speed_avg_buffer = []
        self.ema_speed = None  # Exponential moving average
        self.ema_alpha = 0.05  # Smoothing factor (0.05-0.2 typical)

        # Small label for avg speed (top left of chart)
        self.avg_speed_label = lv.label(self.scrn)
        self.avg_speed_label.set_text("  ")
        self.avg_speed_label.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
        self.avg_speed_label.set_style_text_font(lv.font_montserrat_28, 0)
        # Position: left of chart
        self.avg_speed_label.align_to(self.chart, lv.ALIGN.OUT_TOP_LEFT, 5, -155)

        # Set y-axis range to 0-9 if supported by your LVGL binding
        try:
            self.chart.set_range_min(lv.chart.AXIS.PRIMARY_Y, 0)
            self.chart.set_range_max(lv.chart.AXIS.PRIMARY_Y, 60) # range 0-6 knots
        except AttributeError:
            pass  # Method not available in this LVGL binding
        self.chart.center()
        self.chart.set_point_count(400)
        self.speed_series = self.chart.add_series(lv.palette_main(lv.PALETTE.BLUE), lv.chart.AXIS.PRIMARY_Y)
        self.speed_history = [0] * 20  # Initialize with zeros

        # --- Add event handlers for navigation buttons ---
        self.prev_btn.add_event_cb(self.on_prev_btn, lv.EVENT.CLICKED, None)
        self.next_btn.add_event_cb(self.on_next_btn, lv.EVENT.CLICKED, None)

        # Track which screen is active: 0 = main, 1 = gps, 2 = third
        self.active_screen = 0
        self.gps_scrn = None
        self.third_scrn = None

    def set_display_text(self, text):
        # Ensure text is a string in the form "0.0" to "99.9"
        # Pad with a leading space if needed so decimal is always centered
        if isinstance(text, (float, int)):
            text = f"{text:.1f}"
        if len(text) == 3:  # e.g. "0.0" to "9.9"
            text = f"  {text}" if text[0] == "1" else f" {text}"
        self.d_label.set_text(text)

    def set_compass_text(self, text):
        self.compass_label.set_text(text)

    def update_chart(self, speed):
        # chart requires integers, so multiplied by 10.
        self.speed_avg_buffer.append(speed)

        if len(self.speed_avg_buffer) == 10:
            avg_speed = sum(self.speed_avg_buffer) / 10
            self.chart.set_next_value(self.speed_series, int(avg_speed))
            self.chart.refresh()

            # Update EMA: new_ema = alpha * new_value + (1 - alpha) * old_ema
            if self.ema_speed is None:
                self.ema_speed = avg_speed
            else:
                self.ema_speed = (
                    self.ema_alpha * avg_speed + (1 - self.ema_alpha) * self.ema_speed
                )
            self.avg_speed_label.set_text("{:.1f}".format(self.ema_speed / 10))
            self.speed_avg_buffer.clear()

    # --- Navigation button event handlers ---
    def on_prev_btn(self, evt):
        # Previous: 0 <- 1 <- 2 (wrap around)
        if self.active_screen == 0:
            self.show_third_screen()
        elif self.active_screen == 1:
            lv.screen_load(self.scrn)
            self.active_screen = 0
        elif self.active_screen == 2:
            self.show_gps_screen()

    def on_next_btn(self, evt):
        # Next: 0 -> 1 -> 2 (wrap around)
        if self.active_screen == 0:
            self.show_gps_screen()
        elif self.active_screen == 1:
            self.show_third_screen()
        elif self.active_screen == 2:
            lv.screen_load(self.scrn)
            self.active_screen = 0

    def show_gps_screen(self, latitude=None, longitude=None, satellites_in_use=None, fix_stat=None):
        # Create and show a screen with navigation buttons, lat/lon, and Sat/Fix status
        if not self.gps_scrn:
            self.gps_scrn = lv.obj()
            self.gps_scrn.set_style_bg_color(lv.color_hex(0x000000), 0)
            self.gps_scrn.set_style_text_font(lv.font_montserrat_24, 0)

            gps_label = lv.label(self.gps_scrn)
            gps_label.set_text("GPS")
            gps_label.align(lv.ALIGN.TOP_MID, 0, 20)

            # Latitude label
            self.lat_label = lv.label(self.gps_scrn)
            self.lat_label.set_text("Lat: --")
            self.lat_label.align(lv.ALIGN.CENTER, 0, -30)

            # Longitude label
            self.lon_label = lv.label(self.gps_scrn)
            self.lon_label.set_text("Lon: --")
            self.lon_label.align(lv.ALIGN.CENTER, 0, 30)

            # Satellite & Fix Status label (only on GPS screen)
            self.gps_status_label_gps = lv.label(self.gps_scrn)
            self.gps_status_label_gps.set_text("Sat: --  Fix: --")
            self.gps_status_label_gps.set_style_text_color(lv.color_hex(0xAAAAAA), 0)
            self.gps_status_label_gps.set_style_text_font(lv.font_montserrat_24, 0)
            self.gps_status_label_gps.align(lv.ALIGN.TOP_MID, 0, 60)

            # Add Previous button to GPS screen
            self.gps_prev_btn = lv.button(self.gps_scrn)
            self.gps_prev_btn.set_size(40, 40)
            self.gps_prev_btn.align(lv.ALIGN.BOTTOM_LEFT, 10, -10)
            self.gps_prev_btn.set_style_bg_color(lv.color_hex(0x111111), 0)
            self.gps_prev_btn.set_style_bg_opa(lv.OPA.COVER, 0)
            gps_prev_label = lv.label(self.gps_prev_btn)
            gps_prev_label.set_text(lv.SYMBOL.LEFT)
            self.gps_prev_btn.add_event_cb(self.on_prev_btn, lv.EVENT.CLICKED, None)

            # Add Next button to gps screen
            self.gps_next_btn = lv.button(self.gps_scrn)
            self.gps_next_btn.set_size(40, 40)
            self.gps_next_btn.align(lv.ALIGN.BOTTOM_RIGHT, -10, -10)
            self.gps_next_btn.set_style_bg_color(lv.color_hex(0x111111), 0)
            self.gps_next_btn.set_style_bg_opa(lv.OPA.COVER, 0)
            gps_next_label = lv.label(self.gps_next_btn)
            gps_next_label.set_text(lv.SYMBOL.RIGHT)
            self.gps_next_btn.add_event_cb(self.on_next_btn, lv.EVENT.CLICKED, None)

        # Update latitude and longitude if provided
        if latitude is not None:
            self.lat_label.set_text("Lat: {:.6f}".format(latitude))
        else:
            self.lat_label.set_text("Lat: --")
        if longitude is not None:
            self.lon_label.set_text("Lon: {:.6f}".format(longitude))
        else:
            self.lon_label.set_text("Lon: --")

        # Update Sat/Fix status if provided
        if satellites_in_use is not None and fix_stat is not None:
            fix_map = {0: "No", 1: "Fix", 2: "2D", 3: "3D"}
            fix_str = fix_map.get(fix_stat, str(fix_stat))
            self.gps_status_label_gps.set_text(f"Sat: {satellites_in_use}  Fix: {fix_str}")
        else:
            self.gps_status_label_gps.set_text("Sat: --  Fix: --")

        lv.screen_load(self.gps_scrn)
        self.active_screen = 1

    def show_third_screen(self):
        # Create and show a third screen with navigation buttons and MAC address form
        if not self.third_scrn:
            self.third_scrn = lv.obj()
            self.third_scrn.set_style_bg_color(lv.color_hex(0x111133), 0)
            self.third_scrn.set_style_text_font(lv.font_montserrat_24, 0)

            third_label = lv.label(self.third_scrn)
            third_label.set_text("ESP-NOW Peers")
            third_label.align(lv.ALIGN.TOP_MID, 0, 20)

            # MAC address text area
            self.mac_textarea = lv.textarea(self.third_scrn)
            self.mac_textarea.set_size(300, 120)
            self.mac_textarea.align(lv.ALIGN.CENTER, 0, -20)
            self.mac_textarea.set_text("")  # Will be filled with current peers
            self.mac_textarea.set_placeholder_text("Enter MACs, one per line")

            # Add a touchscreen keyboard for the textarea
            self.mac_kb = lv.keyboard(self.third_scrn)
            self.mac_kb.set_size(300, 120)
            self.mac_kb.align(lv.ALIGN.BOTTOM_MID, 0, 0)
            self.mac_kb.set_textarea(self.mac_textarea)

            # Move navigation and save buttons above the keyboard
            btn_y = -140  # Adjust this value as needed to be above the keyboard

            # Save button
            self.save_btn = lv.button(self.third_scrn)
            self.save_btn.set_size(80, 40)
            self.save_btn.align(lv.ALIGN.CENTER, 0, btn_y)
            self.save_btn.set_style_bg_color(lv.color_hex(0x222222), 0)
            self.save_btn.set_style_bg_opa(lv.OPA.COVER, 0)
            save_label = lv.label(self.save_btn)
            save_label.set_text("Save")
            self.save_btn.add_event_cb(self.on_save_peers, lv.EVENT.CLICKED, None)

            # Add Previous button to third screen
            self.third_prev_btn = lv.button(self.third_scrn)
            self.third_prev_btn.set_size(40, 40)
            self.third_prev_btn.align(lv.ALIGN.BOTTOM_LEFT, 10, btn_y)
            self.third_prev_btn.set_style_bg_color(lv.color_hex(0x111111), 0)
            self.third_prev_btn.set_style_bg_opa(lv.OPA.COVER, 0)
            third_prev_label = lv.label(self.third_prev_btn)
            third_prev_label.set_text(lv.SYMBOL.LEFT)
            self.third_prev_btn.add_event_cb(self.on_prev_btn, lv.EVENT.CLICKED, None)

            # Add Next button to third screen
            self.third_next_btn = lv.button(self.third_scrn)
            self.third_next_btn.set_size(40, 40)
            self.third_next_btn.align(lv.ALIGN.BOTTOM_RIGHT, -10, btn_y)
            self.third_next_btn.set_style_bg_color(lv.color_hex(0x111111), 0)
            self.third_next_btn.set_style_bg_opa(lv.OPA.COVER, 0)
            third_next_label = lv.label(self.third_next_btn)
            third_next_label.set_text(lv.SYMBOL.RIGHT)
            self.third_next_btn.add_event_cb(self.on_next_btn, lv.EVENT.CLICKED, None)

            # Load current peers into textarea
            self.load_peers_to_textarea()

        lv.screen_load(self.third_scrn)
        self.active_screen = 2

    def load_peers_to_textarea(self):
        try:
            with open("/peers.txt") as f:
                peers = [line.strip() for line in f if line.strip()]
        except OSError:
            peers = []
        self.mac_textarea.set_text("\n".join(peers))

    def on_save_peers(self, evt):
        macs = self.mac_textarea.get_text().splitlines()
        macs = [m.strip() for m in macs if m.strip()]
        with open("/peers.txt", "w") as f:
            for mac in macs:
                f.write(mac + "\n")
        # Optionally, show a confirmation
        self.save_btn.set_style_bg_color(lv.color_hex(0x00AA00), 0)
        lv.task_handler()
        import time
        time.sleep_ms(200)
        self.save_btn.set_style_bg_color(lv.color_hex(0x222222), 0)
        # Go to main screen after saving
        lv.screen_load(self.scrn)
        self.active_screen = 0