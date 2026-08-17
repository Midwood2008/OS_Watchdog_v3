#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Watchdog v2.0 - Notification Module
------------------------------------
Centralised alert system (Pushover initially)
"""

import time
import requests
import hashlib


class Notifier:
    def __init__(self, user_key, app_token, cooldown=300):
        self.user_key = user_key
        self.app_token = app_token

        # prevent alert spam
        self.cooldown = cooldown
        self.last_sent = {}

    # -------------------------
    # INTERNAL HELPERS
    # -------------------------

    def _hash(self, title, message):
        return hashlib.md5((title + message).encode()).hexdigest()

    def _can_send(self, key):
        now = time.time()
        last = self.last_sent.get(key, 0)

        return (now - last) > self.cooldown

    def _mark_sent(self, key):
        self.last_sent[key] = time.time()

    # -------------------------
    # PUBLIC SEND METHOD
    # -------------------------

    def send(self, title, message):

        dedupe_key = self._hash(title, message)

        if not self._can_send(dedupe_key):
            print("[PUSHOVER] Suppressed duplicate alert")
            return

        url = "https://api.pushover.net/1/messages.json"

        payload = {
            "token": self.app_token,
            "user": self.user_key,
            "title": title,
            "message": message
        }

        try:
            r = requests.post(url, data=payload, timeout=10)

            if r.status_code == 200:
                print("[PUSHOVER] Sent:", title)
                self._mark_sent(dedupe_key)
            else:
                print("[PUSHOVER] Error:", r.text)

        except Exception as e:
            print("[PUSHOVER] Failed:", e)
