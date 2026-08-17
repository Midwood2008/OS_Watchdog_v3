#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Watchdog v2.0 - MQTT Client Module
Device type is derived from MQTT topic (NOT payload).
"""

import json
import paho.mqtt.client as mqtt

from config import (
    MQTT_BROKER,
    MQTT_PORT,
    MQTT_USER,
    MQTT_PASS,
    MQTT_TOPIC
)


class MQTTHandler:

    def __init__(self, state):

        self.state = state

        self.client = mqtt.Client()

        self.client.username_pw_set(MQTT_USER, MQTT_PASS)

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    # ---------------------------------------------------
    # CONNECT
    # ---------------------------------------------------

    def on_connect(self, client, userdata, flags, rc):

        print("[MQTT] Connected:", rc)

        client.subscribe(MQTT_TOPIC)

        print("[MQTT] Subscribed:", MQTT_TOPIC)

    # ---------------------------------------------------
    # MESSAGE
    # ---------------------------------------------------

    def on_message(self, client, userdata, msg):

        raw = msg.payload.decode(errors="ignore").strip()

        try:
            data = json.loads(raw)

        except Exception:
            print("[MQTT] Non-JSON payload ignored:", raw)
            return

        # -----------------------------
        # DEVICE TYPE FROM TOPIC
        # -----------------------------

        topic_parts = msg.topic.split("/")

        device_type = "UNKNOWN"

        if len(topic_parts) >= 3:

            # milesight / uplink / LT22222 / devEUI
            device_type = topic_parts[2].upper()

        dev_eui = data.get("devEUI", "").lower()

        if not dev_eui:
            return

        # -----------------------------
        # NORMALISE RELAY DATA
        # -----------------------------

        relay_data = {
            "device": data.get("deviceName"),
            "type": device_type,
            "RO1": False,
            "RO2": False
        }

        # -----------------------------
        # LT22222 FORMAT
        # -----------------------------

        if "RO1_status" in data or "RO2_status" in data:

            relay_data["RO1"] = data.get("RO1_status") == "ON"
            relay_data["RO2"] = data.get("RO2_status") == "ON"

        # -----------------------------
        # UC511 FORMAT
        # -----------------------------

        elif "valve_1" in data or "valve_2" in data:

            relay_data["RO1"] = data.get("valve_1") == 1
            relay_data["RO2"] = data.get("valve_2") == 1

        # -----------------------------
        # UNKNOWN FORMAT
        # -----------------------------

        else:

            print("[MQTT] Unknown payload format:", data)
            return

        # -----------------------------
        # UPDATE STATE
        # -----------------------------

        self.state.update_lorawan(dev_eui, relay_data)

        print(
            "[MQTT] {} ({}) RO1={} RO2={}".format(
                relay_data["device"],
                relay_data["type"],
                relay_data["RO1"],
                relay_data["RO2"]
            )
        )

    # ---------------------------------------------------
    # START
    # ---------------------------------------------------

    def start(self):

        self.client.connect(MQTT_BROKER, MQTT_PORT, 60)

        self.client.loop_start()
