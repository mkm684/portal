from awscrt import mqtt
from awsiot import mqtt_connection_builder

import json
import awscallbacks
import configparser

# Create a ConfigParser object
config = configparser.ConfigParser()

# Read the config file
config.read('config.ini')

# Access variables from the config file
default_input_port = config.getint('config', 'default_input_port')
default_endpoint = config.get('config', 'default_endpoint')
default_client_id = config.get('config', 'default_client_id')
default_topic = config.get('config', 'default_topic')
default_test_msg = config.get('config', 'default_test_msg')

project_path = config.get('config', 'project_path')
aws_auth_folder_path = config.get('config', 'aws_auth_folder_path')
default_cert_filepath = config.get('config', 'default_cert_filepath')
default_pri_key = config.get('config', 'default_pri_key')
default_ca_filepath = config.get('config', 'default_ca_filepath')

class PortalDevice():
    def __init__(self, name, mqtt_conn, aws_cb):
        self.mqtt = mqtt_conn
        self.device_name = name
        self.message_topic = default_topic + name
        self.aws_msg_cb = aws_cb

    # Callback when the subscribed topic receives a message
    def on_message_received(self, topic, payload, dup, qos, retain, **kwargs):
        # Check if the payload contains the "message" field
        if 'aws' in str(payload):
            # Message sent from AWS IoT console 
            payload_str = payload.decode('utf-8')
            payload_json = json.loads(payload_str)
            payload_data = payload_json['aws']
            print("Received message from AWS IoT console on topic '{}': {}".format(topic, payload_data))
            self.aws_msg_cb('write', self.device_name, payload_data)
        elif 'portal' in str(payload):
            # Message sent from your application
            print("Received message from topic '{}': {}".format(topic, payload[len("portal:"):]))

    def aws_subsribe(self): 
        # Subscribe
        print("Subscribing to topic '{}'...".format(self.message_topic))
        subscribe_future, packet_id = self.mqtt.subscribe(
            topic=self.message_topic,
            qos=mqtt.QoS.AT_LEAST_ONCE,
            callback=lambda topic, payload, dup, qos, retain: 
                        self.on_message_received(topic, payload, dup, qos, retain))

        subscribe_result = subscribe_future.result()
        print("Subscribed with {}".format(str(subscribe_result['qos'])))
        return subscribe_result
    
    def aws_unsubsribe(self):
        return

    def aws_send_msg(self, msg_payload):
        message_json = json.dumps('portal:' + msg_payload)
        print("sending msg  {}".format(str(message_json)))
        publish_future, packet_id  = self.mqtt.publish(
                    topic=self.message_topic,
                    payload=message_json,
                    qos=mqtt.QoS.AT_LEAST_ONCE)
        return publish_future.result()

# aws main
def start_aws_app():
    ### AWS ###
    # Create a MQTT connection from the command line data
    mqtt_connection = mqtt_connection_builder.mtls_from_path(
        endpoint=default_endpoint,
        port=default_input_port,
        cert_filepath=default_cert_filepath,
        pri_key_filepath=default_pri_key,
        ca_filepath=default_ca_filepath,
        on_connection_interrupted=awscallbacks.on_connection_interrupted,
        on_connection_resumed=awscallbacks.on_connection_resumed,
        client_id=default_clintID,
        clean_session=False,
        keep_alive_secs=30,
        http_proxy_options=None,
        on_connection_success=awscallbacks.on_connection_success,
        on_connection_failure=awscallbacks.on_connection_failure,
        on_connection_closed=awscallbacks.on_connection_closed)

    # Connect
    print(f"Connecting to {default_endpoint} with client ID '{default_clintID}'...")
    connect_future = mqtt_connection.connect()
    connect_future.result()
    print("Connected!")

    return mqtt_connection

def stop_aws_app(mqtt_connection):
    # Disconnect
    print("Disconnecting...")
    disconnect_future = mqtt_connection.disconnect()
    disconnect_future.result()
    print("Disconnected!")
