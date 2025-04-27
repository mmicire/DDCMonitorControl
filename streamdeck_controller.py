#!/usr/bin/env python3

import os
import time
import subprocess
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper
from PIL import Image, ImageDraw, ImageFont

# ========== CONFIG ==========
BUTTONS = [
    {"label": "USB-C",  "input": "0x1b", "group": "input"},
    {"label": "DP1",    "input": "0x0f", "group": "input"},
    {"label": "DP2",    "input": "0x13", "group": "input"},
    {"label": "HDMI1",  "input": "0x11", "group": "input"},
    {"label": "HDMI2",  "input": "0x12", "group": "input"},
    {"label": "Volume", "special": "volume_display", "group": "volume"},
    {"label": "Vol+",   "command": "vol_up", "group": "volume"},
    {"label": "Vol-",   "command": "vol_down", "group": "volume"},
    {"label": "Mute",   "command": "mute_toggle", "group": "volume"},
]

# Color codes
COLORS = {
    "input": "#333333",   # dark gray
    "volume": "#003366",  # dark blue
}

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_SIZE_NORMAL = 14
FONT_SIZE_SMALL = 12
POLL_INTERVAL = 0.05  # seconds
# ========== END CONFIG ==========

# Global state
previous_volume = None
current_input = None
mute_active = False
deck_ref = None

def create_key_image(deck, text, inverted=False, red=False, background_color="black"):
    image = PILHelper.create_image(deck)
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE_SMALL if "\\n" in text else FONT_SIZE_NORMAL)
    except Exception:
        font = ImageFont.load_default()

    if red:
        background = "red"
        foreground = "white"
    elif inverted:
        background = "white"
        foreground = "black"
    else:
        background = background_color
        foreground = "white"

    draw.rectangle((0, 0, image.width, image.height), fill=background)

    lines = text.split("\\n")
    total_height = sum(draw.textbbox((0, 0), line, font=font)[3] for line in lines)
    y = (image.height - total_height) / 2

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        text_position = ((image.width - text_width) / 2, y)
        draw.text(text_position, line, font=font, fill=foreground)
        y += bbox[3]

    return PILHelper.to_native_format(deck, image)

def get_current_volume():
    try:
        result = subprocess.run(["ddcutil", "getvcp", "62"], capture_output=True, text=True, check=True)
        lines = result.stdout.splitlines()
        for line in lines:
            if "current value" in line:
                parts = line.split("=")
                if len(parts) >= 2:
                    value_part = parts[1].strip().split(",")[0]
                    return int(value_part)
    except Exception as e:
        print(f"Error reading current volume: {e}")
    return None

def set_volume(value):
    try:
        value = max(0, min(100, value))
        subprocess.run(["ddcutil", "setvcp", "62", str(value)], check=True)
        print(f"Volume set to {value}")
    except Exception as e:
        print(f"Error setting volume: {e}")

def adjust_monitor_volume(delta):
    global mute_active, previous_volume
    if mute_active and previous_volume is not None:
        print(f"Unmuting from volume control, restoring {previous_volume}")
        set_volume(previous_volume)
        mute_active = False
        update_buttons(deck_ref)

    current_value = get_current_volume()
    if current_value is not None:
        new_value = current_value + delta
        set_volume(new_value)
        update_buttons(deck_ref)

def toggle_mute(deck):
    global previous_volume, mute_active
    current_value = get_current_volume()
    if current_value is None:
        print("Cannot read current volume for mute toggle.")
        return
    if mute_active and previous_volume is not None:
        print(f"Restoring volume to {previous_volume}")
        set_volume(previous_volume)
        mute_active = False
    else:
        print(f"Muting, saving previous volume {current_value}")
        previous_volume = current_value
        set_volume(0)
        mute_active = True
    update_buttons(deck)

def switch_input(deck, input_code):
    try:
        subprocess.run(["ddcutil", "setvcp", "60", input_code], check=True)
        print(f"Switched input to {input_code}")
        time.sleep(1.0)  # NEW: Give monitor time to re-establish DDC/CI
    except Exception as e:
        print(f"Error switching input: {e}")
    update_current_input()
    update_buttons(deck)

def get_current_input():
    try:
        result = subprocess.run(["ddcutil", "getvcp", "60"], capture_output=True, text=True, check=True)
        lines = result.stdout.splitlines()
        for line in lines:
            if "Input Source" in line and "(sl=" in line:
                start = line.find("(sl=") + 4
                end = line.find(")", start)
                input_code = line[start:end]
                return input_code.lower()
    except Exception as e:
        print(f"Error reading current input: {e}")
    return None

def update_current_input():
    global current_input
    current_input = get_current_input()
    print(f"Detected active input: {current_input}")

def run_command(deck, command, button_idx):
    if isinstance(command, str):
        if command == "vol_up":
            adjust_monitor_volume(+1)
        elif command == "vol_down":
            adjust_monitor_volume(-1)
        elif command == "mute_toggle":
            toggle_mute(deck)
    elif isinstance(command, list):
        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running command: {e}")

def key_change_callback(deck, key, state):
    if state and key < len(BUTTONS):
        button = BUTTONS[key]
        if "input" in button:
            switch_input(deck, button["input"])
        elif "command" in button:
            run_command(deck, button["command"], key)

def update_buttons(deck):
    for key, button in enumerate(BUTTONS):
        if key >= deck.key_count():
            break

        inverted = False
        red = False
        background_color = COLORS.get(button.get("group"), "black")

        if "input" in button and current_input and button["input"].lower() == current_input.lower():
            inverted = True

        if button.get("special") == "volume_display":
            vol = get_current_volume()
            if mute_active and vol == 0:
                vol_text = "Volume\\nMUTED"
            elif vol is not None:
                vol_text = f"Volume\\n{vol}%"
            else:
                vol_text = "Volume\\n--%"
            key_image = create_key_image(deck, vol_text, background_color=background_color)
        else:
            if button.get("command") == "mute_toggle" and mute_active:
                red = True
            key_image = create_key_image(deck, button["label"], inverted=inverted, red=red, background_color=background_color)

        deck.set_key_image(key, key_image)

def main():
    global deck_ref
    decks = DeviceManager().enumerate()
    if not decks:
        print("No Stream Decks found.")
        return

    deck = decks[0]
    deck.open()
    deck.reset()
    deck.set_brightness(30)
    deck_ref = deck

    update_current_input()
    update_buttons(deck)

    deck.set_key_callback(key_change_callback)

    try:
        while True:
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        pass
    finally:
        deck.reset()
        deck.close()

if __name__ == "__main__":
    main()
