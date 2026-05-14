# 🛰️ PiSky-OLED By DRSEE

**The companion for AvGeeks to monitor their home ADSB ground station in real-time.**

PiSky-OLED is a dedicated monitoring tool designed for aviation enthusiasts who want a physical dashboard for their ADSB setup. Instead of checking a web interface, you get a live OLED display that identifies the closest aircraft to your antenna, fetches detailed metadata (Registration, Model) via the OpenSky Network API, and keeps track of your station's personal range records. It's the perfect way to keep an eye on your installation's performance and the local sky at a glance.

---

## ✨ Features

*   **Closest Aircraft Focus**: Automatically tracks and displays the nearest plane to your antenna.
*   **Advanced Metadata Enrichment**: Fetches real aircraft models (e.g., "Airbus A321") and registrations (e.g., "F-HFPM") via OpenSky Network.
*   **Smart Caching**: Built-in 24h cache system to respect API rate limits and ensure smooth performance.
*   **Dual-Page Rotating Dashboard**: 
    *   **Page 1 (Sky Overview)**: Total aircraft count and your station's distance range record.
    *   **Page 2 (Closest Focus)**: Live tracking details (Callsign, Reg, Model, Distance, Bearing).
*   **Live Heartbeat**: Visual activity indicator (`*`) to confirm the system is refreshing in real-time.

---

## 🛠️ Prerequisites

### Hardware
1.  **Raspberry Pi** (3, 4, or 5).
2.  **ADSB Receiver** (RTL-SDR Stick + Antenna).
3.  **OLED Display (SSD1306)**: 128x64 pixels, connected via **I2C**.

### Software
*   **ADSB Image**: Optimized for [ADSBExchange](https://www.adsbexchange.com/how-to-feed/) or any OS running `readsb` / `dump1090-fa` with `tar1090`.
*   **Python 3.7+**.
*   **I2C Enabled**: Run `sudo raspi-config` > Interface Options > I2C > Enable.

---

## 🚀 Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone [https://github.com/YOUR_USERNAME/PiSky-OLED.git](https://github.com/YOUR_USERNAME/PiSky-OLED.git)
   cd PiSky-OLED
2. **Install Python dependencies**:
   ```bash
   pip3 install -r requirements.txt
3. **Configure your station**:
   Open `main.py` and enter your local GPS coordinates and preferred settings:
   ```python
   MY_LAT = 46.219696224968246    # Your Station Latitude
   MY_LON = 7.329450323965796     # Your Station Longitude
   ROTATION_SPEED = 10            # Seconds before switching pages
---

## 📂 Project Structure

```text
PiSky-OLED/
├── main.py              # Main orchestrator
├── config.py            # Station & Display settings
├── requirements.txt     # Python dependencies
├── README.md            # Documentation
└── modules/
    ├── __init__.py      # Package initialization
    ├── adsb.py          # Local ADSB data fetcher
    ├── aircraft.py      # OpenSky API & Caching logic
    ├── display.py       # OLED rendering engine
    ├── geo_utils.py     # Distance & Bearing math
    └── system.py        # System monitoring (IP/Temp)
```
---

## 🖥️ Usage

Execute manualy the script to test : 

```bash
python3 main.py
```
---

### 🚀 Run on Boot (Systemd)

To make **PiSky-OLED** start automatically when the Raspberry Pi boots, follow these steps:

1. **Create the service file**:
   ```bash
   sudo nano /etc/systemd/system/pisky.service
2. **Paste the following configuration (ensure your file paths match your installation):**:
    ```bash
    [Unit]
    Description=PiSky OLED Service
    After=network.target

    [Service]
    ExecStart=/usr/bin/python3 /home/pi/PiSky-OLED/main.py
    WorkingDirectory=/home/pi/PiSky-OLED
    StandardOutput=inherit
    StandardError=inherit
    Restart=always
    User=pi

    [Install]
    WantedBy=multi-user.target    
3. **Enable and start the service:**:
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable pisky.service
    sudo systemctl start pisky.service
## 🤝 Contributing
As an aviation enthusiast (**AvGeek**), feel free to fork this project, open issues, or submit pull requests. Every contribution to improve the tracking experience is welcome!

---

## 📜 License
This project is licensed under the **MIT License**.