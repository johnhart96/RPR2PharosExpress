#!/usr/bin/env python3

import socket
import re
from gpiozero import Button
from signal import pause

# ============================================================
# PHAROS NETWORK CONFIG
# ============================================================

PHAROS_IP = "192.168.1.50"
PHAROS_PORT = 50000

# ============================================================
# GPIO INPUT CONFIG
# Safe pins: 4,5,6,12,13,16,17,18,19,20,21,22,23,24,25,26,27
# Format:
# GPIO_PIN : (ON_LABEL, OFF_LABEL)
# ============================================================

INPUTS = {
    17: ("Scene 1", "Off space 1"),
    18: ("Scene 2", "Off space 2"),
    27: ("Scene 3", "Off space 3"),
    22: ("Scene 4", "Off space 4"),
}

# ============================================================
# PHAROS COMMAND GENERATOR
# ============================================================

def generate_pharos_command(label: str) -> str:
    """
    Convert a human-readable label into a Pharos action command.
    """

    text = label.lower().strip()

    # --------------------------------------------------------
    # Activate Scene X
    # Command 1: >C:1,SC:X#
    # --------------------------------------------------------
    match = re.match(r"scene\s+(\d+)", text)
    if match:
        scene = match.group(1)
        return f">C:1,SC:{scene}#"

    # --------------------------------------------------------
    # Turn Off Space Y
    # Command 2: >C:2,S:Y#
    # --------------------------------------------------------
    match = re.match(r"(off\s+space|space\s+\d+\s+off)\s*(\d+)?", text)
    if match:
        space = match.group(2) or re.search(r"\d+", text).group()
        return f">C:2,S:{space}#"

    # --------------------------------------------------------
    # Activate Tag Set / Tag
    # Example label: "Activate tag 1,5"
    # Command 5: >C:5,TS:1,TG:5#
    # --------------------------------------------------------
    match = re.match(r"activate\s+tag\s+(\d+)\s*,\s*(\d+)", text)
    if match:
        tag_set, tag = match.groups()
        return f">C:5,TS:{tag_set},TG:{tag}#"

    # --------------------------------------------------------
    # If no rule matched
    # --------------------------------------------------------
    raise ValueError(f"Unrecognised command label: '{label}'")

# ============================================================
# UDP SETUP
# ============================================================

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def send_udp(command):
    sock.sendto(command.encode("ascii"), (PHAROS_IP, PHAROS_PORT))
    print(f"UDP sent → {command}")

# ============================================================
# GPIO SETUP
# ============================================================

buttons = []

for pin, (on_label, off_label) in INPUTS.items():

    try:
        on_command = generate_pharos_command(on_label)
        off_command = generate_pharos_command(off_label)
    except ValueError as e:
        print(f"Config error on GPIO {pin}: {e}")
        continue

    button = Button(pin, pull_up=True, bounce_time=0.05)

    def make_on_handler(cmd, p, lbl):
        return lambda: (
            print(f"GPIO {p} CLOSED → {lbl}"),
            send_udp(cmd)
        )

    def make_off_handler(cmd, p, lbl):
        return lambda: (
            print(f"GPIO {p} OPEN → {lbl}"),
            send_udp(cmd)
        )

    button.when_pressed = make_on_handler(on_command, pin, on_label)
    button.when_released = make_off_handler(off_command, pin, off_label)

    buttons.append(button)

print("GPIO → Pharos auto-command listener running...")
pause()
``
