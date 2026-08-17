#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Watchdog v2.0 - State Manager 
------------------------------ 
Central in-memory state store for: 
- OpenSprinkler status 
- LoRaWAN relay status 
- Watchdog alarms 
- mismatch timers 
""" 

import time 
import threading 


class WatchdogState:
    """
    Thread-safe shared state container.
    """
    def __init__(self):
        self.lock = threading.Lock()
        # ------------------------- LIVE DEVICE STATE ------------------------- OpenSprinkler: {
        #   "Controller Name": {
        #       "stations": {0: True, 1: False, ...}, "last_poll": timestamp
        #   }
        # }
        self.opensprinkler = {}
        # LoRaWAN: {
        #   "devEUI": {
        #       "RO1": "ON", "RO2": "OFF", "last_seen": timestamp, "device": "name"
        #   }
        # }
        self.lorawan = {}
        # ------------------------- WATCHDOG TRACKING STATE ------------------------- mismatch tracking: key = 
        # mapping_key value = timestamp when mismatch started
        self.mismatch_start = {}
        # alarm state: key = mapping_key value = True/False (already alerted)
        self.alarm_sent = {}
    # ========================================================= OPENSPRINKLER METHODS 
    # =========================================================
    def update_opensprinkler(self, controller_name, stations):
        with self.lock:
            self.opensprinkler[controller_name] = {
                "stations": stations,
                "last_poll": time.time()
            }
    def get_station_state(self, controller_name, station_index):
        with self.lock:
            ctrl = self.opensprinkler.get(controller_name)
            if not ctrl:
                return None
            return ctrl["stations"].get(station_index)
    def get_os_last_seen(self, controller_name):
        with self.lock:
            ctrl = self.opensprinkler.get(controller_name)
            if not ctrl:
                return None
            return ctrl["last_poll"]
    # ========================================================= LORAWAN METHODS 
    # =========================================================
    def update_lorawan(self, dev_eui, data):
        with self.lock:
            self.lorawan[dev_eui] = data
            self.lorawan[dev_eui]["last_seen"] = time.time()
    def get_relay_state(self, dev_eui, relay):
        with self.lock:
            dev = self.lorawan.get(dev_eui)
            if not dev:
                return None
            return dev.get(relay)
    def get_lora_last_seen(self, dev_eui):
        with self.lock:
            dev = self.lorawan.get(dev_eui)
            if not dev:
                return None
            return dev.get("last_seen")
    # ========================================================= WATCHDOG METHODS 
    # =========================================================
    def make_key(self, controller, station, dev):
        return "{}:{}:{}".format(controller, int(station), dev.lower())
    
    def set_mismatch_start(self, key):
        with self.lock:
            if key not in self.mismatch_start:
                self.mismatch_start[key] = time.time()
    def clear_mismatch_start(self, key):
        with self.lock:
            if key in self.mismatch_start:
                del self.mismatch_start[key]
    def get_mismatch_duration(self, key):
        with self.lock:
            start = self.mismatch_start.get(key)
            if not start:
                return 0
            return time.time() - start
    def set_alarm(self, key, value=True):
        with self.lock:
            self.alarm_sent[key] = value
    def get_alarm(self, key):
        with self.lock:
            return self.alarm_sent.get(key, False)
    def reset_alarm(self, key):
        with self.lock:
            self.alarm_sent[key] = False
    # ========================================================= DEBUG HELPERS 
    # =========================================================
    def snapshot(self):
        """
        Safe snapshot for printing/debugging
        """
        with self.lock:
            return {
                "opensprinkler": self.opensprinkler.copy(),
                "lorawan": self.lorawan.copy(),
                "mismatch_start": self.mismatch_start.copy(),
                "alarm_sent": self.alarm_sent.copy()
            }
    def print_summary(self):
        with self.lock:

            print("\n========== CURRENT STATUS ==========")

            print("\nOpenSprinkler:")

            for controller, data in self.opensprinkler.items():
                print(" {}".format(controller))
                print("  Stations:", data.get("stations", {}))

            print("\nLoRaWAN:")

            for dev, data in self.lorawan.items():
                print(
                    " {} RO1={} RO2={}".format(
                        dev,
                        data.get("RO1"),
                        data.get("RO2")
                    )
                )
   
            print("====================================\n")
