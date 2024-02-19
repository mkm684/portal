from awscrt import mqtt, http
from awsiot import mqtt_connection_builder
import sys
import threading
import time
import json
import AWSCallbacks

# received_count = 0
# received_all_event = threading.Event()

#config
default_input_port = 8883
default_endpoint = 'aftrw2t6y8wsg-ats.iot.us-east-2.amazonaws.com'
default_clintID = 'mybasicclientid'
default_topic =  'mytopic/ble/test'
default_test_msg = 'portal: Hello from Portal'

aws_gateway_folder_path = '/home/mohmah/projects/aws-gateway'

def send_aws_msg(msg_topic, msg_payload):
    message_json = json.dumps(msg_payload)
    mqtt_connection.publish(
                topic=msg_topic,
                payload=message_json,
                qos=mqtt.QoS.AT_LEAST_ONCE)

if __name__ == '__main__':
    # Create a MQTT connection from the command line data
    mqtt_connection = mqtt_connection_builder.mtls_from_path(
        endpoint=default_endpoint,
        port=default_input_port,
        cert_filepath=aws_gateway_folder_path + '/gateway.cert.pem',
        pri_key_filepath=aws_gateway_folder_path + '/gateway.private.key',
        ca_filepath=aws_gateway_folder_path + '/root-CA.crt',
        on_connection_interrupted=AWSCallbacks.on_connection_interrupted,
        on_connection_resumed=AWSCallbacks.on_connection_resumed,
        client_id=default_clintID,
        clean_session=False,
        keep_alive_secs=30,
        http_proxy_options=None,
        on_connection_success=AWSCallbacks.on_connection_success,
        on_connection_failure=AWSCallbacks.on_connection_failure,
        on_connection_closed=AWSCallbacks.on_connection_closed)

    print(f"Connecting to {default_endpoint} with client ID '{default_clintID}'...")
    connect_future = mqtt_connection.connect()
    connect_future.result()
    print("Connected!")

    message_topic = default_topic

    # Subscribe
    print("Subscribing to topic '{}'...".format(message_topic))
    subscribe_future, packet_id = mqtt_connection.subscribe(
        topic=message_topic,
        qos=mqtt.QoS.AT_LEAST_ONCE,
        callback=AWSCallbacks.on_message_received)

    subscribe_result = subscribe_future.result()
    print("Subscribed with {}".format(str(subscribe_result['qos'])))

    # on message 
    send_aws_msg(message_topic, default_test_msg)

    time.sleep(100)

    # Disconnect
    print("Disconnecting...")
    disconnect_future = mqtt_connection.disconnect()
    disconnect_future.result()–
    print("Disconnected!")
