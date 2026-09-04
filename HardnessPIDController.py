#By Mantej Dheri
#same code will work for DI-100, DI-1000 or iLoad Series load cells

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
port='FILLOUTPORT'
if port == 'FILLOUTPORT':
  port = input("Please enter a port: ")
try:
  ser = serial.Serial(port=port)
  print("Opening Port {}".format(port))
  if not ser.isOpen:
    ser.open()
  print("Opened Port {}".format(port))
except Exception as e:
  print("Could not open Port {}".format(port))
  print(e)
  ser = None
  
if ser:
  while True:
    ser.write(('W\r').encode('utf-8')) #command to read the weight
    ser.flush()
    out = ''
    time.sleep(0.1)
    while ser.inWaiting() > 0:
        out +=ser.read(1).decode("utf-8")
    try:
      out = float(out)
      print("{} - Port: {}\tData: {}".format(datetime.utcnow().strftime("%m/%d/%y %H:%M:%S.%f"), port, format(out, ".3f")))
    except Exception as e:
      print(e)
      
    

