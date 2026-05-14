import socket
import os
import psutil

class SystemManager:
    def __init__(self):
        pass

    def get_ip_address(self):
        """Get the main local IP address of the Pi"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def get_cpu_temp(self):
        """Get the CPU temperature in Celsius"""
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp = int(f.read()) / 1000
            return f"{temp:.1f}"
        except:
            return "0.0"
            
    def render_system_info(self, temp, ip):
            with canvas(self.device) as draw:
                draw.text((5, 0), "SYSTEM STATUS", fill="white")
                draw.line((0, 12, 128, 12), fill="white")
                
                draw.text((5, 25), f"CPU TEMP: {temp}'C", fill="white")
                draw.text((5, 45), f"IP: {ip}", fill="white")