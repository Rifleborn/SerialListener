import serial
import serial.tools.list_ports
import time
import requests
import re

from serial import SerialException
from bs4 import BeautifulSoup

BAUD_RATE = 9600
APP_VERS_LINK = 'https://script.google.com/macros/s/AKfycbxNLkNEAT9pJltLzODtYa03Jrc7o5pO0mMtY_p_TwohW-R9SVDhbYIgbsJI8rCvkZi7Vw/exec'
PATTERN = r"Temperature:\s*(-?\d+(\.\d+)?),Humidity:\s*(\d+(\.\d+)?),Concentration of gases:\s*(\d+(\.\d+)?),Rain:\s*(\d+(\.\d+)?)"

def find_arduino_port():
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        if "Arduino" in port.description or "CH340" in port.description:
            print(f"Detected Arduino on {port.device}")
            return port.device
    print("No Arduino found, falling back to default COM4")
    return "COM4"

def main():
    serial_port = find_arduino_port()

    try:
        ser = serial.Serial(serial_port, BAUD_RATE, timeout=1)
        print(f"Serial port {serial_port} opened successfully.")

        # Wait for Arduino to initialize
        time.sleep(40)

        while True:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            print(f"[SERIAL] Raw data: {line}")

            match = re.match(PATTERN, line)
            if match:
                try:
                    parts = line.split(",")
                    temp = parts[0].split(":")[1].strip()
                    hum = parts[1].split(":")[1].strip()
                    gases = parts[2].split(":")[1].strip()
                    wetvalue = parts[3].split(":")[1].strip()

                    print(f"Sending → Temp: {temp}, Humidity: {hum}, Gases: {gases}, Wet: {wetvalue}")

                    params = {
                        "sts": "write",
                        "temp": temp,
                        "humd": hum,
                        "gases": gases,
                        "wet": wetvalue,
                    }

                    try:
                        response = requests.get(APP_VERS_LINK, params=params)
                        response.raise_for_status()

                        soup = BeautifulSoup(response.text, "html.parser")
                        visible_text = soup.get_text(strip=True)
                        print("Extracted Text:")
                        print(visible_text)

                    except requests.RequestException as e:
                        print(f"Request failed: {e}")

                except Exception as e:
                    print(f"Parsing error: {e}")
            else:
                print(f"[SERIAL] Ignoring malformed line: {line}")

            time.sleep(15)

    except SerialException as e:
        print(f"Failed to open serial port {serial_port}: {e}")

if __name__ == "__main__":
    main()
