#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Watchdog v2.0 - OpenSprinkler Poller 
------------------------------------- 
Polls OpenSprinkler controllers and updates shared state. 
IMPORTANT: -
 OpenSprinkler uses 0-based station indexing internally. 
- We KEEP 0-based indexing 
everywhere for consistency. 
""" 

import time 
import requests 

from config import OPENSPRINKLERS, POLL_INTERVAL 
from state import WatchdogState 

class OpenSprinklerPoller:
    def __init__(self, state):
        self.state = state
    # ------------------------- SINGLE CONTROLLER POLL -------------------------
    def poll_controller(self, controller):
        url = "http://{}/js".format(controller["ip"])
        params = {"pw": controller["password_md5"]}
        try:
            r = requests.get(url, params=params, timeout=5)
            data = r.json()
            sn = data.get("sn", [])
            # ------------------------- IMPORTANT FIX: KEEP 0-based indexing -------------------------
            stations = {}
            for i, val in enumerate(sn):
                stations[i] = (val == 1)
            self.state.update_opensprinkler(
                controller["name"],
                stations
            )
            print("[OS] {} OK ({})".format(
                controller["name"],
                " ".join(["1" if v else "0" for v in sn])
            ))
        except Exception as e:
            print("[OS] ERROR {}: {}".format(controller["name"], e))
    # ------------------------- MAIN LOOP -------------------------
    def start(self):
        while True:
            for controller in OPENSPRINKLERS:
                self.poll_controller(controller)
            time.sleep(POLL_INTERVAL)
