import time
import ujson
import machine
import neopixel
import random
from umqtt.simple import MQTTClient
from lib.config import load_config
from lib.net import connect as net_connect
import lib.color as color
from lib.animation import animation_type, animation_speed, octants

class XmasTree():
    def __init__(self, config):
        self.config = config
        self.led_count = self.config["pixels"]["count"]
        self.led_pin = self.config["pixels"]["pin"]
        
        self.brightness = 50
        self.pixels = neopixel.NeoPixel(machine.Pin(self.led_pin), self.led_count)
        self.pattern = [(0,0,0)]*self.led_count
        self.animation = animation_type.sparkle
        self.animation_scroll_offset = 0
        self.animation_speed = animation_speed.slow
        self.mqtt = None
        
    def log(self, message, severity = "info"):
        print(severity, message)
        
    def connect(self, stealth=False):
        if not stealth: self.show_status(color.blue)  
        self.log("Starting")
        try:
            net_connect(self.config["wifi"])
        except:
            self.show_status(color.red)
            self.log("resetting due to network connection error","error")
            time.sleep(1)
            machine.reset()
        if not stealth: self.show_status(color.green)
        
        self.mqtt = MQTTClient(
            self.config["mqtt"]["client_name"],
            self.config["mqtt"]["broker"],
            port=self.config["mqtt"]["port"],
            keepalive=300,
            ssl=False,
            user=self.config["mqtt"]["user"],
            password=self.config["mqtt"]["password"])
        self.mqtt.set_callback(self.msg_received)
        self.mqtt.set_last_will(self.config["mqtt"]["base_topic"]+"/status", "offline", retain=True)
        self.mqtt.connect(True)
        
        self.mqtt.subscribe(self.topic("brightness"))
        self.mqtt.subscribe(self.topic("pattern"))
        self.mqtt.subscribe(self.topic("animation"))
        
        self.mqtt.publish(self.topic("status"), "online", retain=True)
        
    def show_status(self, color):
        self.pixels.fill((0,0,0))
        self.pixels[-1] = color
        self.pixels.write()
    
    def topic(self,relative_name):
        return self.config["mqtt"]["base_topic"]+"/"+relative_name
    
    def msg_received(self, topic, msg):
        if topic.decode() == self.topic("brightness"):
            self.set_brightness(msg)
        elif topic.decode() == self.topic("pattern"):
            self.set_pattern(msg)
        elif topic.decode() == self.topic("animation"):
            self.set_animation(msg)
            
    def set_brightness(self, msg):
        str_brightness = msg.decode()
        try:
            b = int(str_brightness)
            if b > 0 and b <= 100:
                self.brightness = b
        except:
            self.log(f"failure while setting brightness to {str_brightness}", error)
    
    def set_pattern(self, msg):
        colors = msg.decode().split(",")
        for i in range(self.led_count):
            color = colors[i % len(colors)]
            try:
                r = int(color[0],16)
                g = int(color[1],16)
                b = int(color[2],16)
                self.pattern[i] = (r,g,b)
            except:
                self.log("invalid color value",error)
        
    def set_animation(self, msg):
        try:
            payload = ujson.loads(msg.decode())
            if "type" in payload:
                if payload["type"] in ("none","sparkle","scroll","swirl"):
                    self.animation = payload["type"]
                else:
                    self.log("unknonw animation in payload", "error")
            if "speed" in payload:
                if payload["speed"] > 0 and payload["speed"] <= 10:
                    self.animation_speed = 1/payload["speed"]
                else:
                    self.log("invalid speed in payload", "error")
        except:
            self.log("Failed to set animation","error")
            
    def apply_brightness(self, color):
        r = int(color[0]*17*self.brightness/100)
        g = int(color[1]*17*self.brightness/100)
        b = int(color[2]*17*self.brightness/100)
        return (r,g,b)
    
    def update(self):
        if self.animation == animation_type.none:
            for index,led in enumerate(self.pattern):
                self.pixels[index] = self.apply_brightness(led)
            self.pixels.write()
            
        if self.animation == animation_type.scroll:
            self.animation_scroll_offset += 1
            for index,led in enumerate(self.pattern):
                self.pixels[(index+self.animation_scroll_offset)%50] = self.apply_brightness(led)
            self.pixels.write()
            
        if self.animation == animation_type.sparkle:
            random_dot = random.randint(0,self.led_count-1)
            for index,led in enumerate(self.pattern):
                self.pixels[index] = self.apply_brightness(led)
            if random.random() > .5:
                backup_dot = self.pixels[random_dot]
                self.pixels[random_dot] = (255,255,255)
                self.pixels.write()
                time.sleep(.05)
                self.pixels[random_dot] = backup_dot
            self.pixels.write()
            
        if self.animation == animation_type.swirl:
            self.animation_scroll_offset += 1
            for index, color in enumerate(self.pattern[:8]):
                for led in octants[(index+self.animation_scroll_offset)%8]:
                    self.pixels[led] = self.apply_brightness(color)
            self.pixels.write()
            
        
    def run(self):
        ticks = 0
        while True:
            ticks += 1
            self.mqtt.check_msg()
            self.update()
            if ticks % 100 == 0:
                self.mqtt.publish(self.topic("uptime"),  str(time.ticks_ms()//1000))
            time.sleep(self.animation_speed)

config = load_config("config.json")
tree = XmasTree(config)

while True:
    try:
        tree.connect()
        tree.run()
    except:
        tree.log("Lost Connection","error")

    
    
        


        



