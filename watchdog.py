#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Watchdog v2.1 - Main Runtime
Clean orchestration layer only.
No logic. No parsing. No polling.
"""

import time
import threading
import json
import paho.mqtt.client as mqtt

from dashboard import start_dashboard

from config import (
    MQTT_BROKER,
    MQTT_PORT,
    MQTT_USER,
    MQTT_PASS,
    MQTT_TOPIC,
    PUSHOVER_USER,
    PUSHOVER_TOKEN
)

from state import WatchdogState
from notifier import Notifier
from opensprinkler import OpenSprinklerPoller
from watchdog_engine import WatchdogEngine
from mqtt_client import MQTTHandler


# =========================================================
# CORE OBJECTS
# =========================================================

state = WatchdogState()

notifier = Notifier(
    PUSHOVER_USER,
    PUSHOVER_TOKEN
)

watchdog = WatchdogEngine(state, notifier)
poller = OpenSprinklerPoller(state)
mqtt = MQTTHandler(state)


# =========================================================
# THREAD WRAPPERS
# =========================================================

def mqtt_thread():
    mqtt.start()


def os_thread():
    poller.start()


def watchdog_thread():
    while True:
        watchdog.check()
        time.sleep(10)


def status_thread():
    while True:
        print("\n--- WATCHDOG STATUS ---")
        state.print_summary()
        time.sleep(60)


def dashboard_thread():
    start_dashboard(state)


# =========================================================
# MAIN
# =========================================================

def main():

    print("======================================")
    print("   WATCHDOG v2.1 STARTING")
    print("======================================")

    print("[INIT] State initialised")
    print("[INIT] MQTT handler ready")
    print("[INIT] OpenSprinkler poller ready")
    print("[INIT] Watchdog engine ready")
    print("[INIT] Dashboard starting...")

    threads = [
        threading.Thread(target=mqtt_thread, daemon=True),
        threading.Thread(target=os_thread, daemon=True),
        threading.Thread(target=watchdog_thread, daemon=True),
        threading.Thread(target=status_thread, daemon=True),
        threading.Thread(target=dashboard_thread, daemon=True),
    ]

    for t in threads:
        t.start()

    print("\n[READY] System running\n")

    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
