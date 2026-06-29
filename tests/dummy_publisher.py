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

# Program constants (topics and connection details)
BROKER = settings.MQTT_BROKER
PORT = settings.MQTT_PORT
TOPIC_TELEMETRY = settings.MQTT_TOPIC_TELEMETRY
TOPIC_STATUS_RELAY = settings.MQTT_TOPIC_STATUS_RELAY

# Control topics matching system specification
TOPIC_CONTROL_FAN = "laboratorium/scada/pv_kit/control/fan"
TOPIC_CONTROL_LAMP = "laboratorium/scada/pv_kit/control/lamp"


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"Connected to MQTT Broker. Subscribing to control topics:")
        print(f" - {TOPIC_CONTROL_FAN}")
        print(f" - {TOPIC_CONTROL_LAMP}")
        client.subscribe(TOPIC_CONTROL_FAN)
        client.subscribe(TOPIC_CONTROL_LAMP)
    else:
        print(f"Failed to connect to broker, return code: {rc}")


def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode("utf-8")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Received control command on {msg.topic}: {payload}")
        data = json.loads(payload)
        
        state_changed = False
        if msg.topic == TOPIC_CONTROL_FAN:
            if "state" in data:
                userdata["relay_fan"] = bool(data["state"])
                state_changed = True
        elif msg.topic == TOPIC_CONTROL_LAMP:
            if "state" in data:
                userdata["relay_lamp"] = bool(data["state"])
                state_changed = True
                
        # If state changed, publish the new status to the status/relay topic (feedback loop)
        if state_changed:
            status_payload = {
                "fan": userdata["relay_fan"],
                "lamp": userdata["relay_lamp"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            client.publish(TOPIC_STATUS_RELAY, json.dumps(status_payload))
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Published status update: {status_payload}")
            
    except Exception as e:
        print(f"Error handling control command: {e}")


def generate_telemetry(state: dict) -> dict:
    # 1. PV Panel Simulation (dependent on simulated sun/randomness)
    pv_v = round(random.uniform(17.0, 21.0), 2)
    pv_i = round(random.uniform(1.5, 3.5), 2)
    pv_p = round(pv_v * pv_i, 2)
    pv_t = round(random.uniform(40.0, 60.0), 1)

    # 2. Inverter Simulation (dependent on relay load controls)
    inv_v = round(random.uniform(218.0, 222.0), 2)
    inv_eff = round(random.uniform(90.0, 95.0), 2)

    # Calculate load power based on state passed via arguments
    # Baseline load (inverter idle draw) = 5W
    # Fan load = 45W, Lamp load = 60W
    load_ac_power = 5.0
    if state["relay_fan"]:
        load_ac_power += 45.0
    if state["relay_lamp"]:
        load_ac_power += 60.0

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
    state["bat_soc"] = round(max(0.0, min(100.0, state["bat_soc"] + (bat_i * 0.05))), 2)

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
            "soc": state["bat_soc"],
            "soc_status": bat_soc_status,
            "t": bat_t,
        },
        "inverter": {"v_ac": inv_v, "i_ac": inv_i, "p_ac": inv_p, "eff": inv_eff},
    }


def main():
    # State dict to store simulation variables (no global keywords used)
    state = {
        "relay_fan": False,
        "relay_lamp": False,
        "bat_soc": 75.0
    }

    # Paho MQTT v2 initialization - passing state as userdata
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, userdata=state)
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"Connecting to MQTT Broker at {BROKER}:{PORT}...")
    try:
        client.connect(BROKER, PORT, keepalive=60)
    except Exception as e:
        print(f"Failed to connect to broker: {e}")
        return

    client.loop_start()
    print("Simulation started. Publishing mock telemetry every 2 seconds. Press Ctrl+C to stop.\n")

    try:
        while True:
            data = generate_telemetry(state)
            payload = json.dumps(data)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Publishing telemetry: {payload}")
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
