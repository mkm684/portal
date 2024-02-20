#!/usr/bin/python3

import dbus

from advertisement import Advertisement
from service import Application, Service, Characteristic, Descriptor

import bluetooth_constants
import bluetooth_utils

GATT_CHRC_IFACE = "org.bluez.GattCharacteristic1"
NOTIFY_TIMEOUT = 5000

adapter_interface = None

devices = {}
managed_objects_found = 0

# classes 
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
        print("ReadValue", options)
        return value
    
    def WriteValue(self, value, options):
        val_decimals = value[:]
        text_string = ''.join(chr(decimal) for decimal in val_decimals)
        # print(text_string)
        print("WriteValue", text_string, options)

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

# functions
def properties_changed(interface, changed, invalidated, path): 
	if interface != bluetooth_constants.GATT_SERVICE_INTERFACE:
		return
    
	if path in devices:
		devices[path] = dict(devices[path].items())
		devices[path].update(changed.items()) 
	else:
		devices[path] = changed
		
	list_connected_devices()

def interfaces_removed(path, interfaces):
	if not bluetooth_constants.GATT_SERVICE_INTERFACE in interfaces:
		return
      
	if path in devices:
		dev = devices[path]
		del devices[path]
		list_connected_devices()
	else:
		print(path, " is not devices to be removed")

def interfaces_added(path, interfaces):
	if not bluetooth_constants.GATT_SERVICE_INTERFACE in interfaces:
		return

	device_properties = interfaces[bluetooth_constants.GATT_SERVICE_INTERFACE] 
	if path not in devices:
		devices[path] = device_properties 
		dev = devices[path]
		list_connected_devices()

def list_connected_devices():
	# Clear the console (optional)
	print("\033[H\033[J")  # For Unix-like systems
	print("Full list of devices",len(devices),"discovered:") 
	print("------------------------------")
	for path in devices:
		dev = devices[path] 
		if 'UUID' in dev:
			info_print = str(bluetooth_utils.dbus_to_python(dev['UUID'])) + " : "
		else:
			info_print = "                  : "
		if 'Device' in dev:
			info_print += str(bluetooth_utils.dbus_to_python(dev['Device'])) + " : "
		else :
			info_print += "                   : "
		print(info_print)

def remove_sig_hndlrs():
	global adapter_interface

	bus = dbus.SystemBus() 
	bus.remove_signal_receiver(interfaces_added,"InterfacesAdded") 
	bus.remove_signal_receiver(interfaces_added,"InterfacesRemoved")
	bus.remove_signal_receiver(properties_changed,"PropertiesChanged")
      
	list_connected_devices()
	return True

def set_sig_hndlrs(bus):
	global adapter_interface
	print('set_sig_hndlrs')

	adapter_path = bluetooth_constants.BLUEZ_NAMESPACE + bluetooth_constants.ADAPTER_NAME

	# acquire an adapter proxy object and its Adapter1 interface so we can call its methods
	adapter_object = bus.get_object('org.bluez', adapter_path)
	adapter_interface=dbus.Interface(adapter_object, 'org.bluez.Adapter1')

	# register signal handler functions so we can asynchronously report discovered devices
	# InterfacesAdded signal is emitted by BlueZ when an advertising packet from a device it doesn't
	# already know about is received
	bus.add_signal_receiver(interfaces_added,
			dbus_interface = bluetooth_constants.DBUS_OM_IFACE,
			signal_name = "InterfacesAdded")

	# InterfacesRemoved signal is emitted by BlueZ when a device "goes away" 
	bus.add_signal_receiver(interfaces_removed,
			dbus_interface = bluetooth_constants.DBUS_OM_IFACE, 
			signal_name = "InterfacesRemoved")

	# PropertiesChanged signal is emitted by BlueZ when something re: a device already encountered
	# changes e.g. the RSSI value 
	bus.add_signal_receiver(properties_changed,
			dbus_interface = bluetooth_constants.DBUS_PROPERTIES, 
			signal_name = "PropertiesChanged",
			path_keyword = "path")
	
# main 
app = Application()
app.add_service(LedService(0))
app.register()

adv = LedAdvertisement(0)
adv.register()

# dbus initialisation steps
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
bus = dbus.SystemBus()
set_sig_hndlrs(bus)

try:
    app.run()
except KeyboardInterrupt:
    app.quit()
