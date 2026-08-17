#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Watchdog v2.0 - Decision Engine
--------------------------------
This module compares OpenSprinkler vs LoRaWAN
states and decides when to alert.
"""

import time

from config import (
    WATCHDOG_MAP,
    MISMATCH_DELAY
)


class WatchdogEngine:

    def __init__(self, state, notifier):
        self.state = state
        self.notifier = notifier

    # ------------------------- MAIN CHECK FUNCTION -------------------------

    def check(self):

        now = time.time()

        for m in WATCHDOG_MAP:

            controller = m["controller"]
            station_index = m["station_index"]
            station_name = m["station_name"]
            dev_eui = m["devEUI"].lower()
            relay = m["relay"]

            key = self.state.make_key(
                controller,
                station_index,
                dev_eui
            )

            # ------------------------- READ CURRENT STATES -------------------------

            os_val = self.state.get_station_state(
                controller,
                station_index
            )

            lora_val = self.state.get_relay_state(
                dev_eui,
                relay
            )

            # If either side missing -> skip safely
            if os_val is None or lora_val is None:
                continue

            lora_on = bool(lora_val)

            # ------------------------- MATCH STATE -------------------------

            if os_val == lora_on:

                # If previously alarmed -> recovery notification
                if self.state.get_alarm(key):

                    self.notifier.send(
                        "Watchdog Recovered",
                        "{}\n{}\nSystem back in sync.".format(
                            controller,
                            station_name
                        )
                    )

                    print(
                        "[WATCHDOG] RECOVERED:",
                        key
                    )

                self.state.reset_alarm(key)
                self.state.clear_mismatch_start(key)

                print(
                    "[MATCH] {} {} -> {}".format(
                        controller,
                        station_name,
                        "ON" if os_val else "OFF"
                    )
                )

                continue

            # ------------------------- MISMATCH STATE -------------------------

            print(
                "[MISMATCH] {} {}".format(
                    controller,
                    station_name
                )
            )

            # Start timer if first seen
            self.state.set_mismatch_start(key)

            elapsed = self.state.get_mismatch_duration(key)

            # Wait for stability window
            if elapsed < MISMATCH_DELAY:
                continue

            # Already alerted?
            if self.state.get_alarm(key):
                continue

            # ------------------------- SEND ALERT -------------------------

            self.notifier.send(
                "Irrigation Watchdog Alert",
                "Controller: {}\nStation: {}\n\n"
                "OpenSprinkler: {}\nLoRaWAN: {}".format(
                    controller,
                    station_name,
                    "ON" if os_val else "OFF",
                    "ON" if lora_on else "OFF"
                )
            )

            self.state.set_alarm(
                key,
                True
            )

            print(
                "[ALERT SENT]",
                key
            )
