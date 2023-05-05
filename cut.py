import json
import printer

p = printer.connect()

with open("config.json","r") as f:
    config: dict = json.load(f)

p = Usb(config["printer"][0], config["printer"][1])
p.cut()