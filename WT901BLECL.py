# -*- coding: utf-8 -*-
#
# this script uses the library bluepy
# install with: pip install bluepy
from bluepy.btle import Peripheral, Scanner, ADDR_TYPE_RANDOM, BTLEDisconnectError, DefaultDelegate
from pprint import pprint
import time
import datetime
import math

class GyroProcessor():
    def __init__(self, data=None):
        # TODO: differentiate between flags  of data 
        # from the differents services that can be configured in the ble device

        # Assuming the packet data is for acceleration, angular velocity and angle Data 
        # (Ignoring the packet header and flag bit)
        hex_data = [ord(el) for el in data[2:]]
        # It is requirement of the manufacturer to cast all values to signed short values, 
        # but python doesnt have this data type, thats why the following transformation exists
        transformed_hex_values = [val if val <= 127 else (256-val)*-1 for val in hex_data]
        for i in range(0,3):
            if i == 0:
                # "Acceleration"
                self.ax = float((int(transformed_hex_values[i+1])<<8)| (int(transformed_hex_values[i]) & 255))/32768*(16*9.8)
                self.ay = float((int(transformed_hex_values[i+3])<<8)| (int(transformed_hex_values[i+2]) & 255))/32768*(16*9.8)
                self.az = float((int(transformed_hex_values[i+5])<<8)| (int(transformed_hex_values[i+4]) & 255))/32768*(16*9.8)

            if i == 1:
                # "Angular Velocity" 
                self.wx = float((int(transformed_hex_values[i+6])<<8)| (int(transformed_hex_values[i+5]) & 255))/32768*2000
                self.wy = float((int(transformed_hex_values[i+8])<<8)| (int(transformed_hex_values[i+7]) & 255))/32768*2000
                self.wz = float((int(transformed_hex_values[i+10])<<8)| (int(transformed_hex_values[i+9]) & 255))/32768*2000
            
            if i == 2:
                # "Angles"
                self.rollx = float((int(transformed_hex_values[i+11])<<8)| (int(transformed_hex_values[i+10]) & 255))/32768*180
                self.pitchy = float((int(transformed_hex_values[i+13])<<8)| (int(transformed_hex_values[i+12]) & 255))/32768*180
                self.yawz = float((int(transformed_hex_values[i+15])<<8)| (int(transformed_hex_values[i+14]) & 255))/32768*180


class DeviceDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    # this portion of code will execute everytime the BLE device emits a notification
    def handleNotification(self, cHandle, data): 
        fecha_actual = datetime.datetime.now()
        processor = GyroProcessor(data)
        ax = processor.ax
        ay = processor.ay
        az = processor.az
        wx = processor.wx
        wy = processor.wy
        wz = processor.wz
        rollx = processor.rollx
        pitchy = processor.pitchy
        yawz = processor.yawz
        print("accel in Y: {}, velocity in x: {}, roll: {}".format(ay, wx, rollx))

#here you can change the bluetooth MAC address of the device
MAC_ble_device = "FF:FF:FF:FF:FF:FF"
addr = False
try:
#it connects to the ble device
    ble_device = Peripheral(MAC_ble_device, ADDR_TYPE_RANDOM,0).withDelegate(DeviceDelegate())
    addr = ble_device.addr
except BTLEDisconnectError:
    print("Trying to reconnect every minute...")
    while not addr:
        try:
            ble_device = Peripheral(MAC_ble_device, ADDR_TYPE_RANDOM,0).withDelegate(DeviceDelegate())
            addr = ble_device.addr
        except:
            pass
        time.sleep(60)
finally:
    print("Connected to {}".format(addr))


# this UUID is the only one with permissions of Write/Read in the device, 
# so I suspect that this is the characteristic I have to modify in order to get the data from the ble device 
UUID_Notification = "0000FFE5-0000-1000-8000-00805F9A34FB"

# extract the services and characteristics of this UUID
ble_service = ble_device.getServiceByUUID(UUID_Notification)
ble_characteristic = ble_service.getCharacteristics()
ble_descriptors = ble_characteristic[0].getDescriptors()
# descriptors values:
# {16: 'NOTIFY', 1: 'BROADCAST', 2: 'READ', 4: 'WRITE NO RESPONSE', 32: 'INDICATE', 8: 'WRITE', 64: 'WRITE SIGNED', 128: 'EXTENDED PROPERTIES'}
# I modify the descriptor with 16 (Notify) in bytes to get the data by notifications
ble_descriptors[0].write(bytes(16))

#principal loop
while True:
    #print("waiting for notifications... \n")
    try:
        # it waits for the ble device 15 seconds and 
        # return True if a notification was emited, False if not
        if ble_device.waitForNotifications(15):
            continue
    except BTLEDisconnectError:
        addr = False
        print("Trying to reconnect every minute...")
        while not addr:
            try:
                ble_device = Peripheral(MAC_ble_device, ADDR_TYPE_RANDOM,0).withDelegate(DeviceDelegate())
                addr = ble_device.addr
            except:
                time.sleep(60)
                pass
            finally:
                print("Connected to {}".format(addr))
    except Exception as e:
        print("an error happened:\n{}".format(e))
    ble_service = ble_device.getServiceByUUID(UUID_Notification)
    ble_characteristic = ble_service.getCharacteristics()
    ble_descriptors = ble_characteristic[0].getDescriptors()
    ble_descriptors[0].write(bytes(16))