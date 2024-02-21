#!/usr/bin/python3
import dbus
import re
import threading

import gi
gi.require_version('GLib', '2.0')
from gi.repository import GLib 

from advertisement import Advertisement
from service import Application, Service, Characteristic, Descriptor

import bluetooth_constants
import blecallbacks

GATT_CHRC_IFACE = "org.bluez.GattCharacteristic1"
NOTIFY_TIMEOUT = 2000

# classes 
class LedAdvertisement(Advertisement):
    def __init__(self, index,):
        Advertisement.__init__(self, index, "peripheral")
        self.add_local_name("LED")
        self.include_tx_power = True

class LedService(Service):
    def __init__(self, index, msg_cb):
        Service.__init__(self, index, bluetooth_constants.LED_SVC_UUID, True)
        self.add_characteristic(LedCharacteristic(self, val_update_cb = msg_cb))

class LedCharacteristic(Characteristic):
    def __init__(self, service, val_update_cb):
        self.notifying = False
        self.localValue = 10
        self.val_chg_cb = val_update_cb
        Characteristic.__init__(
                self, bluetooth_constants.LED_TEXT_CHR_UUID, 
                ["notify", "read", "write"], service)
        
    def ReadValue(self, options):
        value = []
        strtemp = str(self.localValue)
        for c in strtemp:
            value.append(dbus.Byte(c.encode()))
        
        self.localValue = self.localValue + 1
        print("ReadValue", options['device'])
        return value
    
    def WriteValue(self, value, options):
        val_decimals = value[:]
        text_string = ''.join(chr(decimal) for decimal in val_decimals)
        match = re.search(r'dev_(\w+)', options['device'])
        if match:
            dev_name = match.group(1)
        self.val_chg_cb('write', dev_name, text_string)
        print("WriteValue", text_string, dev_name)

    def set_val_callback(self):
        if self.notifying:
            print("sending led notification : " + str(self.localValue)) 
            self.broadcastValue(self.localValue)
            self.localValue = self.localValue + 1

        return self.notifying
    
    def broadcastValue(self, payload):
        value = []
        strtemp = str(payload)
        for c in strtemp:
            value.append(dbus.Byte(c.encode()))
        self.PropertiesChanged(GATT_CHRC_IFACE, {"Value": value}, [])
        return
    
    def sendValue(self, payload, interface):
        # todo : this function is wip to send data to device seperately (broadcast is used for now)
        return
        bus = dbus.SystemBus()
        characteristic_path = bluetooth_constants.BLUEZ_NAMESPACE + bluetooth_constants.ADAPTER_NAME + '/dev_' + interface + '/service001/char002'
        variant_payload = GLib.Variant('s', payload)
        print(variant_payload)
        characteristic_object = bus.get_object("org.bluez", characteristic_path)      
        characteristic_interface = dbus.Interface(characteristic_object, "org.freedesktop.DBus.Properties")
        characteristic_interface.Set("org.bluez.GattCharacteristic1", "Value", dbus.String(payload))

    def StartNotify(self):
        if self.notifying:
            return
        self.notifying = True

    def StopNotify(self):
        self.remove_timeout()
        self.notifying = False
	
# ble main
def ble_app_run(app):
    try:
        app.run()
    except:
        print("An error occurred while running the application.")
    finally:
        app.quit()

def start_ble_app(devices_update_cb, device_msg_cb):     
	app = Application()
	app.add_service(LedService(0, device_msg_cb))
	app.register()

	adv = LedAdvertisement(0)
	adv.register()

	# dbus initialisation steps
	dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
	bus = dbus.SystemBus()
	blecallbacks.set_sig_hndlrs(bus, devices_update_cb)

	# Start the app in a separate thread
	app_thread = threading.Thread(target=ble_app_run, args=(app,))
	app_thread.start()
                
	return app, app_thread, adv

def stop_ble_app():
    blecallbacks.remove_sig_hndlrs()
