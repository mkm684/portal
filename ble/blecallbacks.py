#!/usr/bin/python3
import dbus
import re

import sys
sys.path.append('../ble_utils')

import bluetooth_constants
import bluetooth_utils

devices = {}
managed_objects_found = 0
adapter_interface = None
devices_update_cb_func = None

# functions
def properties_changed(interface, changed, invalidated, path): 
	if interface != bluetooth_constants.GATT_SERVICE_INTERFACE:
		return
    
	if path in devices:
		devices[path] = dict(devices[path].items())
		devices[path].update(changed.items()) 
	else:
		devices[path] = changed
		
	dev = devices[path] 
	match = re.search(r'dev_(\w+)', dev['Device'])
	if match:
		dev_name = match.group(1)

	devices_update_cb_func('updated', dev_name)
	list_connected_devices()

def interfaces_removed(path, interfaces):
	if not bluetooth_constants.GATT_SERVICE_INTERFACE in interfaces:
		return
      
	if path in devices:
		dev = devices[path]
		match = re.search(r'dev_(\w+)', dev['Device'])
		if match:
			dev_name = match.group(1)
			
		devices_update_cb_func('removed', dev_name)
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
		match = re.search(r'dev_(\w+)', dev['Device'])
		if match:
			dev_name = match.group(1)
		devices_update_cb_func('added', dev_name)
		list_connected_devices()

def get_devices():
	return devices

def list_connected_devices():
	# Clear the console (optional)
	# print("\033[H\033[J")  # For Unix-like systems
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

def set_sig_hndlrs(bus, devices_update_cb):
	global adapter_interface
	global devices_update_cb_func
	
	devices_update_cb_func = devices_update_cb
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