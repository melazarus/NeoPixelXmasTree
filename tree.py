from enum import Enum
import paho.mqtt.client as mqtt
import click
from pydantic import BaseSettings, BaseModel
import re
import json


@click.group()
def tree():
    ...


@tree.command()
def rainbow():
    controller = Controller()
    controller.set_pattern(controller.rainbow(leds=50, offset=0))


@tree.command()
@click.argument("pattern", required=True)
def pattern(pattern):
    controller = Controller()
    controller.set_pattern(pattern)


@tree.command()
@click.argument('level', type=click.IntRange(1,100, clamp=True), required=True)
def brightness(level):
    print(f"Setting brightness to {level}%")
    controller = Controller()
    controller.set_brightness(level)

@tree.command()
@click.argument('animation_type', type=click.Choice(['none', 'sparkle', 'scroll', 'swirl'], case_sensitive=False))
@click.option('-s', '--speed', type=click.IntRange(1,10), required=False)
def animation(animation_type, speed):
    controller = Controller()
    controller.set_animation(animation_type, speed)

class TreeAnimation(Enum):
    none = "none"
    sparkle = "sparkle"
    scroll = "scroll"


class TreeAnimationDirection(Enum):
    up = "up"
    down = "down"


class TreeAnimationSpeed(Enum):
    slow = "slow"
    fast = "fast"


class Controller:
    def __init__(self) -> None:
        self._client = None
        self._settings = None

    @property
    def client(self):
        if not self._client:
            client = mqtt.Client()
            client.username_pw_set(self.settings.MQTT_USER, self.settings.MQTT_PASS)
            client.connect(self.settings.MQTT_BROKER, self.settings.MQTT_PORT, keepalive=60)
            self._client = client
        return self._client

    @property
    def settings(self):
        if not self._settings:
            self._settings = Settings()
        return self._settings

    def publish(self, topic, payload, qos, retain):
        return self.client.publish(
            f"{self.settings.base_topic}/{topic}", payload=payload, qos=qos, retain=retain
        )

    def set_pattern(self, pattern: str):
        if not re.match("[0-9A-F]{3}(,[0-9A-F]{3})*",pattern.upper()):
            raise Exception(f"Invalid color pattern {pattern}")
        self.publish("pattern", payload=pattern.upper(), qos=1, retain=True)

    def set_brightness(self, brightness: int):
        self.publish("brightness", payload=str(brightness), qos=1, retain=True)

    def set_animation(self, animation_type, speed):
        payload = {"type":animation_type, "speed":speed or 5}
        self.publish("animation", payload=json.dumps(payload), qos=1, retain=True)

    @staticmethod
    def rainbow(leds, offset=0):
        rising = lambda x: int(15 * (x))
        dropping = lambda x: int(15 * (1 - x))

        # reglar HSV https://www.instructables.com/How-to-Make-Proper-Rainbow-and-Random-Colors-With-/
        colors = []
        for i in range(leds):
            i_offset = (i + offset) % leds
            chunk = i_offset // (leds / 6)
            chunk_index = (i_offset - (chunk * (leds / 6))) / (leds / 6)
            if chunk == 0:
                r = 15
                g = rising(chunk_index)
                b = 0
            if chunk == 1:
                r = dropping(chunk_index)
                g = 15
                b = 0
            if chunk == 2:
                r = 0
                g = 15
                b = rising(chunk_index)
            if chunk == 3:
                r = 0
                g = dropping(chunk_index)
                b = 15
            if chunk == 4:
                r = rising(chunk_index)
                g = 0
                b = 15
            if chunk == 5:
                r = 15
                g = 0
                b = dropping(chunk_index)

            colors.append(hex(r)[2:] + hex(g)[2:] + hex(b)[2:])
        return ",".join(colors)


class Settings(BaseSettings):
    MQTT_BROKER: str
    MQTT_PORT: int
    MQTT_USER: str
    MQTT_PASS: str
    base_topic: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "XMAS_TREE_"
        fields = {
            "MQTT_BROKER": {"env": "MQTT_BROKER"},
            "MQTT_PORT": {"env": "MQTT_PORT"},
            "MQTT_USER": {"env": "MQTT_USER"},
            "MQTT_PASS": {"env": "MQTT_PASS"},
            "base_topic": {"env": "BASE_TOPIC"},
        }


class LedSettings(BaseModel):
    pattern: list[str] = ["000"]
    # animation: TreeAnimation = TreeAnimation.none
    # animation_color: str = ""
    # animation_direction: TreeAnimationDirection = TreeAnimationDirection.up
    # animation_speed: TreeAnimationSpeed = TreeAnimationSpeed.slow


if __name__ == "__main__":
    tree()
