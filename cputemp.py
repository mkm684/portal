#!/usr/bin/python3

"""Copyright (c) 2019, Douglas Otwell

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import dbus

from advertisement import Advertisement
from service import Application, Service, Characteristic, Descriptor
from gpiozero import CPUTemperature
from dbus import Byte, Array, Signature
import bluetooth_constants

GATT_CHRC_IFACE = "org.bluez.GattCharacteristic1"
NOTIFY_TIMEOUT = 5000

class ThermometerAdvertisement(Advertisement):
    def __init__(self, index):
        Advertisement.__init__(self, index, "peripheral")
        self.add_local_name("Thermometer")
        self.include_tx_power = True

class LedAdvertisement(Advertisement):
    def __init__(self, index,):
        Advertisement.__init__(self, index, "peripheral")
        self.add_local_name("LED")
        self.include_tx_power = True

class LedService(Service):
    def __init__(self, index):
        Service.__init__(self, index, bluetooth_constants.LED_SVC_UUID, True)
        self.add_characteristic(LedCharacteristic(self))

class LedCharacteristic(Characteristic):
    def __init__(self, service):
        self.notifying = False
        self.localValue = 10
        Characteristic.__init__(
                self, bluetooth_constants.LED_TEXT_CHR_UUID, 
                ["notify", "read", "write"], service)
        
    def ReadValue(self, options):
        value = []
        strtemp = str(self.localValue)
        for c in strtemp:
            value.append(dbus.Byte(c.encode()))
        
        self.localValue = self.localValue + 1
        return value
    
    def WriteValue(self, value, options):
        val_decimals = value[:]
        text_string = ''.join(chr(decimal) for decimal in val_decimals)
        print(text_string)

    def set_val_callback(self):
        if self.notifying:
            print("sending led notification : " + str(self.localValue)) 
            value = []
            strtemp = str(self.localValue)
            for c in strtemp:
                value.append(dbus.Byte(c.encode()))
            self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])
            self.localValue = self.localValue + 1

        return self.notifying

    def StartNotify(self):
        if self.notifying:
            return
        self.notifying = True
        self.set_val_callback()
        self.add_timeout(NOTIFY_TIMEOUT, self.set_val_callback)

    def StopNotify(self):
        self.remove_timeout()
        self.notifying = False

class ThermometerService(Service):
    THERMOMETER_SVC_UUID = "00000001-710e-4a5b-8d75-3e5b444bc3cf"

    def __init__(self, index):
        self.farenheit = True

        Service.__init__(self, index, self.THERMOMETER_SVC_UUID, True)
        self.add_characteristic(TempCharacteristic(self))
        self.add_characteristic(UnitCharacteristic(self))

    def is_farenheit(self):
        return self.farenheit

    def set_farenheit(self, farenheit):
        self.farenheit = farenheit

class TempCharacteristic(Characteristic):
    TEMP_CHARACTERISTIC_UUID = "00000002-710e-4a5b-8d75-3e5b444bc3cf"

    def __init__(self, service):
        self.notifying = False

        Characteristic.__init__(
                self, self.TEMP_CHARACTERISTIC_UUID,
                ["notify", "read"], service)
        self.add_descriptor(TempDescriptor(self))

    def get_temperature(self):
        value = []
        unit = "C"

        cpu = CPUTemperature()
        temp = cpu.temperature
        if self.service.is_farenheit():
            temp = (temp * 1.8) + 32
            unit = "F"

        strtemp = str(round(temp, 1)) + " " + unit
        for c in strtemp:
            value.append(dbus.Byte(c.encode()))

        return value

    def set_temperature_callback(self):
        if self.notifying:
            value = self.get_temperature()
            self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])

        return self.notifying

    def StartNotify(self):
        if self.notifying:
            return

        self.notifying = True

        value = self.get_temperature()
        self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])
        self.add_timeout(NOTIFY_TIMEOUT, self.set_temperature_callback)

    def StopNotify(self):
        self.notifying = False

    def ReadValue(self, options):
        value = self.get_temperature()

        return value

class TempDescriptor(Descriptor):
    TEMP_DESCRIPTOR_UUID = "2901"
    TEMP_DESCRIPTOR_VALUE = "CPU Temperature"

    def __init__(self, characteristic):
        Descriptor.__init__(
                self, self.TEMP_DESCRIPTOR_UUID,
                ["read"],
                characteristic)

    def ReadValue(self, options):
        value = []
        desc = self.TEMP_DESCRIPTOR_VALUE

        for c in desc:
            value.append(dbus.Byte(c.encode()))

        return value

class UnitCharacteristic(Characteristic):
    UNIT_CHARACTERISTIC_UUID = "00000003-710e-4a5b-8d75-3e5b444bc3cf"

    def __init__(self, service):
        Characteristic.__init__(
                self, self.UNIT_CHARACTERISTIC_UUID,
                ["read", "write"], service)
        self.add_descriptor(UnitDescriptor(self))

    def WriteValue(self, value, options):
        val = str(value[0]).upper()
        val_decimals = value[:]
        text_string = ''.join(chr(decimal) for decimal in val_decimals)
        if val == "C":
            print("celusis now")
            self.service.set_farenheit(False)
        elif val == "F":
            print("fehrinhiet now")
            self.service.set_farenheit(True)
        else:
            print(text_string)

    def ReadValue(self, options):
        value = []

        if self.service.is_farenheit(): val = "F"
        else: val = "C"
        value.append(dbus.Byte(val.encode()))

        return value

class UnitDescriptor(Descriptor):
    UNIT_DESCRIPTOR_UUID = "2901"
    UNIT_DESCRIPTOR_VALUE = "Temperature Units (F or C)"

    def __init__(self, characteristic):
        Descriptor.__init__(
                self, self.UNIT_DESCRIPTOR_UUID,
                ["read"],
                characteristic)

    def ReadValue(self, options):
        value = []
        desc = self.UNIT_DESCRIPTOR_VALUE

        for c in desc:
            value.append(dbus.Byte(c.encode()))

        return value

app = Application()
app.add_service(ThermometerService(0))
app.add_service(LedService(1))
app.register()

adv = ThermometerAdvertisement(0)
adv.register()

# adv2 = LedAdvertisement(1)
# adv2.register()

try:
    app.run()
except KeyboardInterrupt:
    app.quit()
