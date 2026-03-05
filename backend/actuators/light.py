import logging
try:
    import RPi.GPIO as GPIO
    MOCK = False
except ImportError:
    MOCK = True
    logging.warning("RPi.GPIO not available, using mock mode for light control")

from backend.config import config_repository

logger = logging.getLogger(__name__)

class LightActuator:
    def __init__(self, pin: int = 17):
        self.pin = pin
        if is_raspberry_pi():
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            GPIO.setup(self.pin, GPIO.OUT)
            GPIO.output(self.pin, GPIO.LOW)  # Assume LOW is off

    def turn_on(self):
        if MOCK:
            logger.info("MOCK: Turning light ON")
        else:
            GPIO.output(self.pin, GPIO.HIGH)
            logger.info("Turning light ON")

    def turn_off(self):
        if MOCK:
            logger.info("MOCK: Turning light OFF")
        else:
            GPIO.output(self.pin, GPIO.LOW)
            logger.info("Turning light OFF")

    def cleanup(self):
        if not MOCK:
            GPIO.cleanup(self.pin)
