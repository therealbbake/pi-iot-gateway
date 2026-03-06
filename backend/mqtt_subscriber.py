import logging
import threading
import ssl
from paho.mqtt import client as mqtt_client

from backend.config import config_repository
from backend.actuators.light import LightActuator

logger = logging.getLogger(__name__)

class MQTTSubscriber:
    def __init__(self):
        self.settings = config_repository.settings.transport
        self.secrets = config_repository.secrets
        self.client = mqtt_client.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.light = LightActuator()
        self.host = self.settings.mqtt_host if not self.settings.mqtt_use_tls else f"{self.settings.domain}.device.iot.{self.settings.region}.oci.oraclecloud.com"
        self.port = self.settings.mqtt_port if not self.settings.mqtt_use_tls else 8883
        self.topics = {
            "/light/on": self.light.turn_on,
            "/light/off": self.light.turn_off
        }
        self.connected = False
        self.status = "disabled"
        if self.settings.mqtt_use_tls:
            self.client.username_pw_set(self.secrets.external_key, self.secrets.secret)
            context = ssl.create_default_context()
            self.client.tls_set_context(context)
            self.client.tls_insecure_set(False)

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("Connected to MQTT broker")
            self.connected = True
            self.status = "connected"
            for topic in self.topics.keys():
                client.subscribe(topic)
                logger.info(f"Subscribed to {topic}")
        else:
            logger.error(f"Failed to connect, return code {rc}")
            self.connected = False
            self.status = "failed"

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        if topic in self.topics:
            try:
                self.topics[topic]()
                status = "on" if topic == "/light/on" else "off"
                client.publish("/light/status", f'{{"light": "{status}"}}', qos=1)
            except Exception as e:
                logger.error(f"Error handling message on {topic}: {e}")
                client.publish("/light/status", f'{{"error": "{str(e)}"}}', qos=1)

    def start(self):
        if config_repository.settings.transport.protocol == "mqtt":
            self.status = "connecting"
            try:
                self.client.connect(self.host, self.port, 60)
                threading.Thread(target=self.client.loop_forever, daemon=True).start()
            except Exception as e:
                logger.error(f"Failed to connect to MQTT broker: {e}")
                self.status = "failed"
        else:
            logger.info("MQTT subscriber not started: protocol not set to 'mqtt'")
            self.status = "disabled"

    def stop(self):
        self.client.disconnect()
        self.light.cleanup()
