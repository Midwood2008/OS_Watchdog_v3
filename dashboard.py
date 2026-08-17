#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, render_template_string
import time

app = Flask(__name__)

# Injected state from watchdog.py #1e3dle
state = None


HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Watchdog Dashboard</title>
    <meta http-equiv="refresh" content="30">

    <style>
        body { font-family: Arial; background: #3B3A39; color: #eee; }
        .box { padding: 10px; margin: 10px; border-radius: 15px; }
        .match { background: #145214; }
        .mismatch { background: #4a1f1f; }
        .neutral { background: #222; }
        .active { background: #2a2a4a; }
        .osactive { background: #145214;}
        table { width: 100%; border-collapse: collapse; }
        td { padding: 6px; border-bottom: 1px solid #333; }

        h2 { margin-top: 20px; border-bottom: 1px solid #444; }
    </style>
</head>
<body>

<h1>🌱 Watchdog Control Dashboard</h1>

<h2>🚨 MISMATCH / MATCH STATUS</h2>

{% for m in mismatches %}
<div class="box mismatch">
    <b>{{ m.controller }} - {{ m.name }}</b><br>
    Station {{ m.station }} | Relay {{ m.relay }}<br>
    OS: {{ "ON" if m.os else "OFF" }} |
    LoRa: {{ "ON" if m.lora else "OFF" }}<br>
    ⏱ Mismatch: {{ m.mismatch_age }} sec
</div>
{% endfor %}

{% for m in matches %}
<div class="box match">
    <b>{{ m.controller }} - {{ m.name }}</b><br>
    Station {{ m.station }} | Relay {{ m.relay }}<br>
    Status: MATCH
</div>
{% endfor %}

<h2>⚡ ACTIVE LORAWAN RELAYS</h2>

{% for d in active_lora %}
<div class="box active">
    <b>{{ d.device }}</b><br>
    RO1={{ "ON" if d.RO1 else "OFF" }} |
    RO2={{ "ON" if d.RO2 else "OFF" }}
</div>
{% endfor %}

<h2>🌱 OPENSPRINKLER STATUS</h2>

{% for ctrl, stations in active_os.items() %}
<div class="box osactive">
    <b>{{ ctrl }}</b>

    <table>
    {% for st in stations %}
        <tr>
            <td>Station {{ st }}</td>
            <td><b>ON</b></td>
        </tr>
    {% endfor %}
    </table>
</div>
{% endfor %}

</body>
</html>
"""


@app.route("/")
def index():

    global state

    if state is None:
        return "State not attached"

    snapshot = state.snapshot()

    os_state = snapshot["opensprinkler"]
    lora_state = snapshot["lorawan"]
    mismatch_start = snapshot["mismatch_start"]

    from config import WATCHDOG_MAP

    mapped = []
    now = time.time()

    # -------------------------------
    # BUILD MAPPED VIEW
    # -------------------------------
    for m in WATCHDOG_MAP:

        ctrl = m["controller"]
        station = m["station_index"]
        name = m["station_name"]
        dev = m["devEUI"].lower()
        relay = m["relay"]

        os_val = os_state.get(ctrl, {}).get("stations", {}).get(station, False)

        lo_val = lora_state.get(dev, {}).get(relay, None)

        # normalize safety
        if lo_val is None:
            lo_val_bool = False
        else:
            lo_val_bool = bool(lo_val)

        key = "{}:{}:{}".format(ctrl, station, dev)

        mismatch_time = mismatch_start.get(key)
        mismatch_age = int(now - mismatch_time) if mismatch_time else 0

        mapped.append({
            "controller": ctrl,
            "station": station,
            "name": name,
            "dev": dev,
            "relay": relay,
            "os": os_val,
            "lora": lo_val_bool,
            "match": os_val == lo_val_bool,
            "mismatch_age": mismatch_age
        })

    # -------------------------------
    # SORTING
    # -------------------------------

    mismatches = sorted(
        [x for x in mapped if not x["match"]],
        key=lambda x: x["mismatch_age"],
        reverse=True
    )

    matches = [x for x in mapped if x["match"]]

    # -------------------------------
    # ACTIVE LORAWAN DEVICES
    # -------------------------------

    active_lora = [
        {**lora_state[dev], "dev": dev}
        for dev in lora_state
        if lora_state[dev].get("RO1") or lora_state[dev].get("RO2")
    ]

    # -------------------------------
    # RENDER
    # -------------------------------
    active_os = {}

    for ctrl, data in os_state.items():

        running = []

        for st, val in data["stations"].items():
            if val:
                running.append(st)

        if running:
            active_os[ctrl] = running


    return render_template_string(
        HTML,
        mismatches=mismatches,
        matches=matches,
        active_lora=active_lora,
        active_os=active_os,
        lora=lora_state
    )


def start_dashboard(shared_state):

    global state
    state = shared_state

    app.run(host="0.0.0.0", port=5000, debug=False)
