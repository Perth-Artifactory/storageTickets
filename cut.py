import json
import requests

with open("config.json","r") as f:
    config: dict = json.load(f)

d = []
d.append({"command": "cut"})
requests.put(config["escpos-web"], json=d)