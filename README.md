# StreamDeck Monitor and Audio Controller

This project lets you use a Stream Deck (via HID) on Linux to control:

- Monitor input selection (USB-C, DP1, DP2, HDMI1, HDMI2)
- Monitor speaker volume (via DDC/CI)
- Mute/unmute monitor speakers
- Show current volume or "MUTED" on the Stream Deck

👉 No proprietary software required.

---

## 🌟 Features

- Dynamic button display:
  - Inputs show active source (highlighted).
  - Volume percentage shown live.
  - Mute button turns red when muted.
- Group coloring (inputs = gray, volume controls = blue).
- Easy to extend and modify.

---

## 📦 Requirements

- Python 3
- `python3-pillow`
- `python3-streamdeck`
- `ddcutil`
- Linux (Debian, Ubuntu, Arch, etc.)

### Install packages:

```bash
sudo apt install python3-pip ddcutil
pip3 install pillow StreamDeck
```

**Note:**
You must have permission to access `/dev/hidraw*` devices
(usually automatic for desktop users, or add your user to `plugdev` group).

---

## ⚡ Quick Start

```bash
chmod +x streamdeck_controller.py
./streamdeck_controller.py
```

👉 Your Stream Deck will light up and control your monitor!

---

## 🔥 Install as a systemd Service (Optional)

Run your controller automatically at boot:

1. Create the service file:

```bash
sudo nano /etc/systemd/system/streamdeck-controller.service
```

Paste:

```ini
[Unit]
Description=StreamDeck Controller Service
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/path/to/your/script
ExecStart=/path/to/your/script/streamdeck_controller.py
Restart=always
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

👉 Replace `YOUR_USERNAME` and `/path/to/your/script` accordingly.

2. Reload systemd:

```bash
sudo systemctl daemon-reload
```

3. Enable the service:

```bash
sudo systemctl enable streamdeck-controller.service
```

4. Start it now:

```bash
sudo systemctl start streamdeck-controller.service
```

---

## 🧐 Notes

- `ddcutil` must detect your monitor.
- Volume and input switching requires DDC/CI enabled on your monitor (check monitor settings).
- Stream Deck must be accessible to user (check `/dev/hidraw*` permissions if needed).
