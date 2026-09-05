# 2. Identify the scale Port
# - mac (ls /dev/ |grep usb)
#   You are looking for a device that starts with "cu.usbserial"
#     ie. /dev/tty.usbserial-A600fby
# - open device manager and expand ports
#     ie. COM36
# 4. Update code to specify the exact device (Found on Line 4)

import time
import serial
from datetime import datetime


class HardnessPIDController:

    def __init__(self):
        self.ser = None

    def open(self):

        port='COM3'

        if port == 'FILLOUTPORT':
            port = input("Please enter a port: ")

        try:
            self.ser = serial.Serial(port=port)
            print("Opening Port {}".format(port))

            if not self.ser.is_open:
                self.ser.open()

            print("Opened Port {}".format(port))

        except Exception as e:
            print("Could not open Port {}".format(port))
            print(e)
            self.ser = None

    def get_weight(self):
        if self.ser:

            self.ser.write(('W\r').encode('utf-8'))
            self.ser.flush()

            out = ''
            time.sleep(0.1)

            while self.ser.in_waiting > 0:
                out += self.ser.read(1).decode("utf-8")


            try:
                out = float(out)
                return out

            except Exception as e:
                print(e)
                return None

        return None

    def close(self):

        if self.ser:
            self.ser.close()
            self.ser = None


if __name__ == '__main__':

    controller = HardnessPIDController()
    controller.open()
    while True:

        weight = controller.get_weight()

        if weight is not None:
            print("Data: {}".format(
                format(weight, ".3f")
            ))

        time.sleep(0.1)