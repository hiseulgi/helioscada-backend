import time
import json
import random
from datetime import datetime, timezone
import paho.mqtt.client as mqtt

BROKER = "localhost"
PORT = 1883
TOPIC = "laboratorium/scada/pv_kit/telemetry"


def generate_telemetry():
    pv_v = round(random.uniform(15.0, 21.0), 2)
    pv_i = round(random.uniform(0.0, 3.5), 2)
    pv_p = round(pv_v * pv_i, 2)
    pv_t = round(random.uniform(35.0, 65.0), 1)

    bat_v = round(random.uniform(11.0, 14.2), 2)
    bat_i = round(random.uniform(-2.5, 3.0), 2)
    bat_p = round(bat_v * bat_i, 2)
    bat_soc = round(random.uniform(50.0, 100.0), 2)
    bat_soc_status = random.choice(["Coulomb Counting", "Calibrated via Lookup Table"])
    bat_t = round(random.uniform(25.0, 38.0), 1)

    inv_v = round(random.uniform(215.0, 225.0), 2)
    inv_i = round(random.uniform(0.05, 0.8), 2)
    inv_p = round(inv_v * inv_i, 2)
    inv_eff = round(random.uniform(88.0, 97.0), 2)

    fan = random.choice([True, False])
    lamp = random.choice([True, False])

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pv": {"v": pv_v, "i": pv_i, "p": pv_p, "t": pv_t},
        "battery": {
            "v": bat_v,
            "i": bat_i,
            "p": bat_p,
            "soc": bat_soc,
            "soc_status": bat_soc_status,
            "t": bat_t
        },
        "inverter": {"v_ac": inv_v, "i_ac": inv_i, "p_ac": inv_p, "eff": inv_eff},
        "relay": {"fan": fan, "lamp": lamp}
    }


def main():
    # Paho MQTT v2 initialization
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    
    print(f"Connecting to MQTT Broker at {BROKER}:{PORT}...")
    try:
        client.connect(BROKER, PORT, keepalive=60)
    except Exception as e:
        print(f"Failed to connect to broker: {e}")
        return

    client.loop_start()
    print("Simulation started. Publishing mock data every 2 seconds. Press Ctrl+C to stop.")
    
    try:
        while True:
            data = generate_telemetry()
            payload = json.dumps(data)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Publishing: {payload}")
            client.publish(TOPIC, payload)
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nStopping simulation...")
    finally:
        client.loop_stop()
        client.disconnect()
        print("Simulation stopped.")


if __name__ == "__main__":
    main()
