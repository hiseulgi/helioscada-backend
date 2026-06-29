import json
import os
import random
import sys
import time
from datetime import datetime, timezone

# Add the project root directory to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import paho.mqtt.client as mqtt

from src.backend.app.core.config import settings

# Load configuration from centralized settings
BROKER = settings.MQTT_BROKER
PORT = settings.MQTT_PORT
TOPIC_TELEMETRY = settings.MQTT_TOPIC_TELEMETRY
TOPIC_RELAY = settings.MQTT_TOPIC_STATUS_RELAY

# Global simulated state
relay_fan = False
relay_lamp = False
bat_soc = 75.0  # Initial State of Charge (%)


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(
            f"Connected to MQTT Broker. Subscribing to relay control topic: {TOPIC_RELAY}"
        )
        client.subscribe(TOPIC_RELAY)
    else:
        print(f"Failed to connect to broker, return code: {rc}")


def on_message(client, userdata, msg):
    global relay_fan, relay_lamp
    try:
        payload = msg.payload.decode("utf-8")
        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] Received relay control command: {payload}"
        )
        data = json.loads(payload)

        # Update global relay states if they are present in the command
        if "fan" in data:
            relay_fan = bool(data["fan"])
        if "lamp" in data:
            relay_lamp = bool(data["lamp"])

    except Exception as e:
        print(f"Error handling relay command: {e}")


def generate_telemetry():
    global bat_soc, relay_fan, relay_lamp

    # 1. PV Panel Simulation (dependent on simulated sun/randomness)
    pv_v = round(random.uniform(17.0, 21.0), 2)
    # Give PV some current if it's daylight (simulated as always sunny for simplicity)
    pv_i = round(random.uniform(1.5, 3.5), 2)
    pv_p = round(pv_v * pv_i, 2)
    pv_t = round(random.uniform(40.0, 60.0), 1)

    # 2. Inverter Simulation (dependent on relay load controls)
    inv_v = round(random.uniform(218.0, 222.0), 2)
    inv_eff = round(random.uniform(90.0, 95.0), 2)

    # Calculate load power based on relay state
    # Baseline load (inverter idle draw) = 5W
    # Fan load = 25W, Lamp load = 40W
    load_ac_power = 0.0
    if relay_fan:
        load_ac_power += 25.0
    if relay_lamp:
        load_ac_power += 10.0

    inv_p = round(load_ac_power, 2)
    inv_i = round(inv_p / inv_v, 2)

    # 3. Battery Simulation (dependent on net power)
    bat_v = round(random.uniform(12.2, 12.8), 2)

    # Battery DC power: PV charging power minus Inverter DC draw (divided by inverter efficiency)
    inv_dc_draw = inv_p / (inv_eff / 100.0)
    bat_p_net = pv_p - inv_dc_draw

    bat_p = round(bat_p_net, 2)
    bat_i = round(bat_p_net / bat_v, 2)

    # Update state of charge (SoC) based on net battery current
    # Charge/discharge rate factor adjusted for fast-paced simulation feedback
    bat_soc = round(max(0.0, min(100.0, bat_soc + (bat_i * 0.05))), 2)

    # SoC status description
    bat_soc_status = (
        "Coulomb Counting" if abs(bat_i) > 0.2 else "Calibrated via Lookup Table"
    )

    # Temperature rises slightly with higher charge/discharge current
    bat_t = round(25.0 + abs(bat_i) * 1.2 + random.uniform(-0.5, 0.5), 1)

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pv": {"v": pv_v, "i": pv_i, "p": pv_p, "t": pv_t},
        "battery": {
            "v": bat_v,
            "i": bat_i,
            "p": bat_p,
            "soc": bat_soc,
            "soc_status": bat_soc_status,
            "t": bat_t,
        },
        "inverter": {"v_ac": inv_v, "i_ac": inv_i, "p_ac": inv_p, "eff": inv_eff},
    }


def main():
    # Paho MQTT v2 initialization
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"Connecting to MQTT Broker at {BROKER}:{PORT}...")
    try:
        client.connect(BROKER, PORT, keepalive=60)
    except Exception as e:
        print(f"Failed to connect to broker: {e}")
        return

    client.loop_start()
    print(
        "Simulation started. Publishing mock data every 2 seconds. Press Ctrl+C to stop.\n"
    )

    try:
        while True:
            data = generate_telemetry()
            payload = json.dumps(data)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Publishing: {payload}")
            client.publish(TOPIC_TELEMETRY, payload)
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nStopping simulation...")
    finally:
        client.loop_stop()
        client.disconnect()
        print("Simulation stopped.")


if __name__ == "__main__":
    main()
