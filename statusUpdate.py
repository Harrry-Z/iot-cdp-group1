# Periodically submit the state obtained by the sensors to the cloud
# and update the shadow

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
import logging
import time
import json
from sense_hat import SenseHat

# aws iot shadow schema
#
# {
#     "state: {
#         "desired": {
#             "temperature":"38.5",
#               "humidity":"60"
#         }
#         "reported": {
#             "timestamp":"2020-04-13 10:07:43",
#               "temperature":"37",
#               "humidity":"30",
#               "level":"yes|no"
#         }
#     }
# }


# Initialize Sense Hat
sense = SenseHat()
# fetch data from sense hat
# get current time
currenttime = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())
# temperature
temp = sense.get_temperature()
# humidity
humidity = sense.get_humidity()
temp = round(temp, 1)
humidity = round(humidity, 1)

# Display humidity and temp readings
print("Moisture Level: {}".format(humidity))
print("Temperature: {}".format(temp))

#level
raw = sense.accel_raw
x = raw["x"]
y = raw["y"]
z = raw["z"]
print (x,y,z)
level_str = "x: " + str(x) + ", y: " + str(y) + ", z: " + str(z)
level_state = "no"
if (-0.05 < x < 0.05) and (-0.05 < y < 0.05) and (0.95 < z < 1.05):
    level_state = "yes"
# orientation = sense.get_orientation_degrees()
# print(orientation)
    

def getDeviceStatus():
    temp = sense.get_temperature()
    humidity = sense.get_humidity()
    temp = round(temp, 1)
    humidity = round(humidity, 1)
    # level
    raw = sense.accel_raw
    x, y, z = raw["x"], raw["y"], raw["z"]
    level_str = "x: " + str(x) + ", y: " + str(y) + ", z: " + str(z)
    level_state = "no"
    if (-0.05 < x < 0.05) and (-0.05 < y < 0.05) and (0.95 < z < 1.05):
        level_state = "yes"
    # time
    currenttime = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())
    result = {"temperature":temp, "humidity":humidity, "level":level_state, "time":currenttime}
    print(result)
    return result
     

def sendCurrentState2AWSIoT():
    #check current status of device
    currentStatus = getDeviceStatus()
    # print("Device current status is " + currentStatus)
    print("Sending reported status to MQTT...")
    temp = currentStatus["temperature"]
    humidity = currentStatus["humidity"]
    level = currentStatus["level"]
    currentTime = currentStatus["time"]
    jsonPayload = {"state": {"reported": {"timestamp":str(currentTime),"temperature":str(temp),"humidity":str(humidity),"level":str(level)}}}
    print(str(jsonPayload))
    deviceShadowHandler.shadowUpdate(json.dumps(jsonPayload), customShadowCallback_upate, 50)
 

def customShadowCallback_upate(payload, responseStatus, token):
    # payload is a JSON string which will be parsed by jason lib
    if responseStatus == "timeout":
        print("Update request with " + token + " time out!")
    if responseStatus == "accepted":
        playloadDict = json.loads(payload)
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        print(payload)
        print("Update request with token: " + token + " accepted!")
        print("Temperature: " + str(playloadDict["state"]["reported"]["temperature"]))
        print("humidity: " + str(playloadDict["state"]["reported"]["humidity"]))
        print("level: " + str(playloadDict["state"]["reported"]["level"]))
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n\n")
    if responseStatus == "rejected":
        print("Update request " + token + " rejected!")

def printDeviceStatus():
    print("=========================")
    status = getDeviceStatus()
    print(" Current status: " + str(status))
    print("=========================\n\n")

# aws iot info
awsiotHost = "a1eeyktzyeh5hs-ats.iot.us-east-1.amazonaws.com"
awsiotPort = 443;
rootCAPath = "/home/pi/Scripts/lab3/crt/root-ca-cert.pem"
privateKeyPath = "/home/pi/Scripts/lab3/crt/ac354bff74-private.pem.key"
certificatePath = "/home/pi/Scripts/lab3/crt/ac354bff74-certificate.pem.crt"

myAWSIoTMQTTShadowClient = None;
myAWSIoTMQTTShadowClient = AWSIoTMQTTShadowClient("Status Update")
myAWSIoTMQTTShadowClient.configureEndpoint(awsiotHost, awsiotPort)
myAWSIoTMQTTShadowClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

myAWSIoTMQTTShadowClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTShadowClient.configureConnectDisconnectTimeout(60) # 10sec
myAWSIoTMQTTShadowClient.configureMQTTOperationTimeout(30) #5sec

#connect to AWS IoT
myAWSIoTMQTTShadowClient.connect()

#create a devcie Shadow with persistent subscription
thingName = "my-iot-thing"
deviceShadowHandler = myAWSIoTMQTTShadowClient.createShadowHandlerWithName(thingName, True)

#update shadow in a loop
loopCount = 0
while True:
    sendCurrentState2AWSIoT()
    time.sleep(15)
