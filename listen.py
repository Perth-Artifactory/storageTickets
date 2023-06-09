import json
import sys
import time
from datetime import datetime, timedelta
from pprint import pprint

import keyboard
import requests
import printer

from slack_bolt import App

time.sleep(30)

with open("config.json","r") as f:
    config: dict = json.load(f)

# Initiate Slack client
app = App(token=config["slack"]["bot_token"])

p = printer.connect()

# take a filename and resize it to a specific width and autoscaled height. Returns the PIL object
def resize_image(filename: str, width: int):
    from PIL import Image
    img = Image.open(filename)
    wpercent = (width / float(img.size[0]))
    hsize = int((float(img.size[1]) * float(wpercent)))
    img = img.resize((width, hsize), Image.ANTIALIAS)
    return img

def text_size(n: int) -> None:
    p.set(smooth=True,
        width=n,
        height=n)

def format_param(key: str, value: str) -> None:
    text_size(1)
    p.text("{}: ".format(key))
    text_size(2)
    if "___" in value:
        text_size(3)
        print("blank line?")
    p.text("{}\n".format(value))

def print_parking_ticket(contact: dict = "Visitor", rules: str = ""):
    p.image(img_source=resize_image(f'./img/{config["logo"]}', 576),
            impl="bitImageRaster")
    text_size(3)
    p.text("Storage Auth\n")
    format_param("Name", contact["name"])
    format_param("Phone", contact["phone"])
    format_param("Date left", datetime.now().strftime("%d/%m %H:%M"))
    format_param("Latest pickup", (datetime.now() + timedelta(days=3)).strftime("%a %d/%m %H:%M"))
    text_size(1)
    p.text("\nRules:\n")
    for line in rules:
        p.text(line+"\n")
    p.text("\nEvents within 4 days:\n")
    for event in get_events():
        p.text(f'{event["summary"]}: {event["start"].strftime("%d/%m %H:%M")}\n')
    p.cut()

def print_slack_invite() -> None:
    p.image(img_source=resize_image("logo_wide.png", 576),
            impl="bitImageRaster")
    p.set(smooth=True,
        width=2,
        height=2)
    p.text("Join our slack!\n")
    p.set(smooth=True,
        width=1,
        height=1)
    p.qr("https://perart.io/slack",size=8)
    p.cut()

def get_contact(key: str) -> str:
    global keys
    """Get the name of the person with the given key from TidyHQ"""
    # Get all fresh door keys from TidyHQ
    if key not in keys:
        print("Key not found, refreshing from tidyauth just in case")
        r = requests.get(f'{config["tidyauth_address"]}/api/v1/keys/contacts', params={"token":config["tidyauth_token"], "update": "tidyhq"})
        keys = reorder_keys(r.json())
    if key not in keys:
        return {'name': '___________',
                'phone': '__________',
                'tag': key}
    return keys[key]

# Accepts a string and formats it so that each line is no longer than 48 characters
def format_text(text: str) -> list:
    lines = []
    line = ""
    for word in text.split(" "):
        if len(line) + len(word) > 48:
            lines.append(line.strip())
            line = ""
        line += word + " "
    lines.append(line)
    return lines

# Downloads a json file containing a list of upcoming events and returns a list of any events in the next n days
def get_events(n: int = 4) -> list[dict]:
    try:
        r = requests.get(config["events"])
        events = r.json()
    except:
        return []
    upcoming_events = []
    for event in events:
        if datetime.strptime(event["start"], "%Y-%m-%dT%H:%M:%S+08:00") < datetime.now() + timedelta(days=n):
            event["start"] = datetime.strptime(event["start"], "%Y-%m-%dT%H:%M:%S+08:00")
            event["end"] = datetime.strptime(event["end"], "%Y-%m-%dT%H:%M:%S+08:00")
            upcoming_events.append(event)
    return upcoming_events

def reorder_keys(keys: dict) -> dict:
    new_keys = {}
    for key in keys:
        if keys[key].get("tag"):
            new_keys[keys[key]["tag"]] = keys[key]
    return new_keys

def send_slack(contact):
    slack_str = ""
    if "slack" in contact:
        slack_str = f'<@{contact["slack"]}>'
        app.client.chat_postMessage(
            channel=contact["slack"],
            text=f'G\'day {slack_str}, it looks like you\'ve printed a ticket to leave a project in the space.\nAs a reminder this ticket will expire on {(datetime.now() + timedelta(days=3)).strftime("%a %m-%d %H:%M")}.\nIf you want you can use `/remind` to create a reminder for yourself :slightly_smiling_face:'
        )
    else:
        contact["name"] = contact["tag"]
    app.client.chat_postMessage(
        channel=config["slack"]["notification_channel"],
        text=f'{slack_str} ({contact["name"]}) has printed a project parking auth ticket'
    )

# Format rules

rules = """* Projects can be left in the space for up to 3 days after last use.
* Project must be left on a single trestle table with name, contact details, and date of pickup.
* Project must be in a movable state as events/workshops have priority over the area.
* Your project may be discarded if it doesn't meet these requirements."""
rule_lines = []
for rule in rules.split("\n"):
    rule_lines += format_text(rule)

# Prefetch keys
print("Prefetching keys")
r = requests.get(f'{config["tidyauth_address"]}/api/v1/keys/contacts', params={"token":config["tidyauth_token"], "update": "tidyhq"})
keys = reorder_keys(r.json())
print(f'Got {len(keys)} keys')
print("Listening for key scans")

while True:
    recorded = keyboard.record(until='enter')
    s = ""
    for x in recorded:
        if x.event_type == "down" and x.name != "enter":
            s+=x.name
    print(s)
    if len(s) == 20:
        s = s[10:]
    if len(s) == 10:
        contact = get_contact(key=s)
        pprint(contact)
        print_parking_ticket(contact=contact,rules=rule_lines)
        send_slack(contact)
