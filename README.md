#  PiSky-OLED By DRSEE

**The companion for AvGeeks to monitor their home ADSB ground station in real-time.**

PiSky-OLED is a dedicated monitoring tool designed for aviation enthusiasts who want a physical dashboard for their ADSB setup. Instead of checking a web interface, you get a quick live OLED display featuring a GNS-style **Moving Map**, a **Radar Homing** needle for the closest traffic, and detailed aircraft metadata.

---

##  Features

* **Four-Page Dynamic Dashboard**:
* **Page 1 (Sky Overview)**: Total aircraft count and your station's all-time distance range record.
* **Page 2 (Closest Focus)**: Detailed text data for the nearest plane (Callsign, Registration, Model, Distance).
* **Page 3 (Radar Homing)**: A visual compass/needle pointing directly toward the closest aircraft, updating in real-time (**0.5s refresh**).
* **Page 4 (Moving Map)**: A minimalist, vector-based radar screen showing all nearby traffic with **Dynamic Scaling** (arrow size adjusts based on zoom).


* **Advanced Metadata Enrichment**: Fetches real aircraft models (e.g., "Airbus A321") and registrations via the OpenSky Network API.
* **Smart Logic & Refresh**:
* Static pages stay for 5s.
* Dynamic pages (Radar/Map) stay for 15s with high-frequency updates for smooth motion.


* **Toggleable Labels**: Option to hide callsigns on the map for a cleaner "stealth" look.

---

##  Prerequisites

### Hardware

1. **Raspberry Pi** (3, 4, 5).
2. **ADSB Receiver** (RTL-SDR Stick + Antenna).
3. **OLED Display (SSD1306)**: 128x64 pixels, connected via **I2C**.

### Software

* **ADSB Image**: Optimized for [ADSBExchange](https://www.adsbexchange.com/how-to-feed/) or any OS running `readsb` / `dump1090-fa`.
* **Python 3.7+**.
* **I2C Enabled**: `sudo raspi-config` > Interface Options > I2C > Enable.

---

##  Installation & Setup

1. **Clone the repository**:
```bash
git clone https://github.com/YOUR_USERNAME/PiSky-OLED.git
cd PiSky-OLED
```


2. **Install Python dependencies**:
```bash
pip3 install -r requirements.txt
```


3. **Configure your station**:
Open `main.py` to set your coordinates and preferences:
```python
MY_LAT = 46.219696224968246    # Your Station Latitude
MY_LON = 7.329450323965796     # Your Station Longitude
PAGE_DURATIONS = {0: 5, 1: 5, 2: 15, 3: 15} # Seconds per page
```



---

##  Project Structure

```text
PiSky-OLED/
├── main.py              # Main orchestrator (Loop & Logic)
├── requirements.txt     # Python dependencies
├── README.md            # Documentation
└── modules/
    ├── __init__.py      # Package initialization
    ├── adsb.py          # Data fetcher (Parses aircraft.json)
    ├── aircraft.py      # OpenSky API & Caching logic
    ├── display.py       # OLED Rendering engine (Maps, Radar, Text)
    ├── geo_utils.py     #  (Distance, Bearing, Projections)
    └── system.py        # System monitoring (IP/Temp)

```

---

##  Usage

Run the script manually to test:

```bash
python3 main.py

```

###  Run on Boot (Systemd)

To make **PiSky-OLED** start automatically:

1. **Create the service file**:
```bash
sudo nano /etc/systemd/system/pisky.service

```


2. **Paste the configuration**:
```ini
[Unit]
Description=PiSky OLED Service
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/PiSky-OLED/main.py
WorkingDirectory=/home/pi/PiSky-OLED
Restart=always
User=pi

[Install]
WantedBy=multi-user.target

```


3. **Enable and start**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable pisky.service
sudo systemctl start pisky.service

```



---

##  Contributing

As an aviation enthusiast (**AvGeek**), feel free to fork this project, open issues, or submit pull requests. Every contribution to improve the tracking experience is welcome!

---

##  License

This project is licensed under the **MIT License**.