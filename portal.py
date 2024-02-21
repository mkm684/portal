import select
import time
import sys

import blegateway
import awsgateway
import bluetooth_constants

from awsgateway import PortalDevice

portaldevices = {}
aws_mqtt = None
ble_app = None

def aws_msg_update_cb(dir, dev_name, payload):
    global ble_app
    print("aws_msg_update_cb", dir, dev_name, payload)
    if dir == 'read':
        #todo : for aws to request a msg from ble
        pass
    elif dir == 'write':
        ble_app.services[0].characteristics[0].broadcastValue(payload)
        pass  
    return

def ble_devices_change_cb(action, dev_name):
    print("ble_devices_change_cb", action, dev_name)
    global aws_mqtt
    if action == 'added':
        portaldevices[dev_name] = PortalDevice(dev_name, aws_mqtt, aws_msg_update_cb)
        portaldevices[dev_name].aws_subsribe()
    elif action == 'removed':
        portaldevices[dev_name].aws_unsubsribe()
        del portaldevices[dev_name]
    elif action == 'updated':
        #todo
        pass
    return

def ble_msg_update_cb(dir, dev_name, payload): 
    print("ble_devices_change_cb", dir, dev_name, payload)
    if dir == 'read': 
        #todo : for ble to request a msg from aws
        pass
    elif dir == 'write':
        portaldevices[dev_name].aws_send_msg(payload)
    return

if __name__ == '__main__':
    aws_mqtt = awsgateway.start_aws_app()
    ble_app, ble_app_thread, ble_adv = blegateway.start_ble_app(ble_devices_change_cb, ble_msg_update_cb)

    # Main loop
    while True: 
        user_input = input("Press 'e' to exit the loop: ")
        if user_input == 'e':
            ble_app.quit()
            ble_app_thread.join()
            awsgateway.stop_aws_app
            blegateway.stop_ble_app
            break  # Exit the loop if the user enters 'e'
    
    sys.exit()
