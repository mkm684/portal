# Portal IoT Gateway
The Portal IoT Gateway is an infrastructure solution designed to connect network devices with BLE IoT devices to stream data to the cloud, such as AWS or Google Cloud. This infrastructure serves as a backbone for IoT-embedded applications, particularly for devices equipped with BLE connectivity, aiming to optimize costs while enabling seamless data streaming and remote control capabilities.

# Overview
The exacts of this project are made of a Raspberry 4 that runs Raspian. The PI utilizes Bluez library and its dependencies like Dbus to control the PI BLE device built in. The project also connects to AWS Iot Core service and streams data to it. BLE service is advertised and devices can connect automatically and stream data directly to AWS Iot topics. Connection is established from the device side and AWS topics are automatically created after.

# Features
## BLE Connectivity: 
The gateway supports BLE connectivity, enabling seamless communication with IoT devices equipped with BLE technology.
## Cloud Integration: 
Stream data from IoT devices to cloud platforms such as AWS or Google Cloud for storage, analysis, and visualization.
## Remote Control: 
Enable remote management and control of IoT devices from anywhere, empowering users to interact with their devices remotely.
## Scalability: 
The infrastructure is designed to scale efficiently to accommodate a growing number of IoT devices and increasing data volumes.
## Security: 
Implement robust security measures to protect data integrity and ensure secure communication between devices and the cloud.

# Getting Started
The project is based on Raspberry or any other running Linux Soc equipped with a BLE device that can be controlled via DBUS and the Bluez library. 
To use the Portal IoT Gateway, follow these steps:
## Hardware Setup: 
- Connect the PI to your network and ensure it has access to the internet.
- Use any BLE GATT device for testing (nrf connect on any phone).
- Install the Bluez library on the PI. 

## Cloud Configuration: 
- Setup AWS account and add the AWS iot core service. 
- connect AWS iot core to the pi via this guide. 
https://docs.aws.amazon.com/iot/latest/developerguide/connecting-to-existing-device.html
- configure your project path in the aws/config.ini. 
- copy your aws file gateway.cert.pem, gateway.private.key, root-CA.crt into the aws_auth. Feel free to change the path of these files in the config file. 

## Dependencies 
- Install the Bluez library using the following command 
    '''pip install pybluez''''

## Usage
- start the portal using these commands. 
    '''python portal.py''''
- start your device and connect to the advertised GATT service. 
- Subscribe to the topic printed on the terminal on the AWS MQTT client. 
- Send data from the BLE device, to see it on the MQTT interface. 
- Send data from AWS to view it on the BLE device. 
- Connect multiple BLE devices subscribe to newly created topics automatically and communicate with the device from AWS. 

# Contributing
Contributions to the Portal IoT Gateway project are welcome! If you have ideas for improvements or new features, feel free to submit pull requests or open issues on the GitHub repository.

# License
The Portal IoT Gateway is licensed under the GNU License.

# Support
For any inquiries or assistance regarding the Portal IoT Gateway, please contact mohamed.mahmoud@mun.ca



