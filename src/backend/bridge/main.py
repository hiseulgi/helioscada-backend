import asyncio
import json
import logging
import sys
import paho.mqtt.client as mqtt
import httpx
from src.backend.app.core.config import settings

# Configure logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("mqtt_bridge")

# Thread-safe queue to pass messages from MQTT client thread to Asyncio main thread
message_queue = asyncio.Queue()
main_loop = None

# Global state to track relay changes and avoid duplicate logs
last_relay_state = {"fan": None, "lamp": None}


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        logger.info(f"Successfully connected to MQTT Broker at {settings.MQTT_BROKER}:{settings.MQTT_PORT}")
        # Subscribe to telemetry topic upon successful connection
        client.subscribe(settings.MQTT_TOPIC_TELEMETRY)
        client.subscribe(settings.MQTT_TOPIC_STATUS_RELAY)
        logger.info(f"Subscribed to topics: {settings.MQTT_TOPIC_TELEMETRY}, {settings.MQTT_TOPIC_STATUS_RELAY}")
    else:
        logger.error(f"Failed to connect to MQTT Broker, return code: {rc}")


def on_disconnect(client, userdata, flags, rc, properties=None):
    logger.warning(f"Disconnected from MQTT Broker (code: {rc}). Automatic reconnection in progress...")


def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode("utf-8")
        logger.debug(f"Received raw MQTT message on {msg.topic}: {payload}")
        
        # Schedule queue insert on the main asyncio event loop from the MQTT thread
        if main_loop and not main_loop.is_closed():
            main_loop.call_soon_threadsafe(message_queue.put_nowait, (msg.topic, payload))
    except Exception as e:
        logger.error(f"Error handling incoming MQTT message: {e}")


async def process_queue(http_client: httpx.AsyncClient):
    global last_relay_state
    logger.info("Queue processor task started.")
    while True:
        topic, payload = await message_queue.get()
        try:
            # Parse payload to ensure it is valid JSON
            data = json.loads(payload)
            
            if topic == settings.MQTT_TOPIC_TELEMETRY:
                logger.info("Forwarding telemetry payload to API...")
                url = f"{settings.API_URL}/telemetry"
                response = await http_client.post(url, json=data, timeout=5.0)
                
                if response.status_code == 201:
                    logger.info(f"Telemetry successfully written to DB via API. Log ID: {response.json().get('id')}")
                else:
                    logger.error(f"API returned error code {response.status_code}: {response.text}")
                    
            elif topic == settings.MQTT_TOPIC_STATUS_RELAY:
                timestamp = data.get("timestamp")
                for device in ["fan", "lamp"]:
                    if device in data:
                        current_state = data[device]
                        # Only log if the state actually changed
                        if last_relay_state[device] != current_state:
                            # If it's the very first time we get state, just sync without logging it as a user action
                            if last_relay_state[device] is not None:
                                control_payload = {
                                    "timestamp": timestamp,
                                    "device": device,
                                    "action": "ON" if current_state else "OFF",
                                    "status": "SUCCESS"
                                }
                                logger.info(f"Forwarding control action payload to API for {device}...")
                                url = f"{settings.API_URL}/control"
                                response = await http_client.post(url, json=control_payload, timeout=5.0)
                                if response.status_code == 201:
                                    logger.info(f"Control action logged via API. Log ID: {response.json().get('id')}")
                                else:
                                    logger.error(f"API returned error code {response.status_code}: {response.text}")
                            
                            # Update the internal state tracker
                            last_relay_state[device] = current_state
        except json.JSONDecodeError:
            logger.error(f"Received invalid JSON format on MQTT broker: {payload}")
        except httpx.RequestError as exc:
            logger.error(f"API connection error when forwarding to {settings.API_URL}: {exc}")
        except Exception as e:
            logger.error(f"Unexpected error in queue processor: {e}")
        finally:
            message_queue.task_done()


async def main():
    global main_loop
    main_loop = asyncio.get_running_loop()
    
    logger.info("Initializing MQTT-to-API Bridge Daemon...")
    
    # Initialize Paho MQTT Client (v2 API)
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    
    # Configure reconnection delay (min 1 sec, max 2 min)
    client.reconnect_delay_set(min_delay=1, max_delay=120)
    
    # Connect to broker (automatic reconnect handles failures afterward)
    try:
        client.connect(settings.MQTT_BROKER, settings.MQTT_PORT, keepalive=60)
    except Exception as e:
        logger.error(f"Could not initiate connection to MQTT Broker ({settings.MQTT_BROKER}:{settings.MQTT_PORT}): {e}")
        logger.info("Reconnection routine will automatically attempt to reconnect in the background.")
        
    # Start MQTT loop in background thread
    client.loop_start()
    
    try:
        # Create persistent client session to reuse connection pooling
        async with httpx.AsyncClient() as http_client:
            await process_queue(http_client)
    except asyncio.CancelledError:
        logger.info("Bridge daemon cancellation request received.")
    finally:
        logger.info("Cleaning up bridge daemon resources...")
        client.loop_stop()
        client.disconnect()
        logger.info("Bridge daemon stopped successfully.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bridge daemon terminated by keyboard interrupt.")
