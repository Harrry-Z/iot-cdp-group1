# 文件 ledController.py 充当Led 灯的控制器，
# 它定期向Led 发出『开』或『关』的指令，并定期获取其状态

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
import logging
import time
import json
import threading
from sense_hat import SenseHat

# aws iot shadow schema
# 
# Name: Led
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

deviceShadowHandler = None
# Initialize Sense Hat
# ########
sense = SenseHat()

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
    return {"temperature":temp, "humidity":humidity, "level":level_state, "time":currenttime}


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


def customShadowCallback_delete(payload, responseStatus, token):
    if responseStatus == "timeout":
        print("Delete request " + token + " time out!")
    if responseStatus == "accepted":
        print("Delete request with token " + token + " accepted!")
    if responseStatus == "rejected":
        print("Delete request with token " + token + " rejected!")

# # Cofigure logging
# logger = logging.getLogger("AWSIoTPythonSDK.core")
# logger.setLevel(logging.ERROR)
# streamHandler = logging.StreamHandler()
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# streamHandler.setFormatter(formatter)
# logger.addHandler(streamHandler)

# aws iot info
awsiotHost = "a1eeyktzyeh5hs-ats.iot.us-east-1.amazonaws.com"
awsiotPort = 443;
rootCAPath = "/home/pi/Scripts/lab3/crt/root-ca-cert.pem"
privateKeyPath = "/home/pi/Scripts/lab3/crt/ac354bff74-private.pem.key"
certificatePath = "/home/pi/Scripts/lab3/crt/ac354bff74-certificate.pem.crt"

myAWSIoTMQTTShadowClient = None;
myAWSIoTMQTTShadowClient = AWSIoTMQTTShadowClient("Status Initialization")
myAWSIoTMQTTShadowClient.configureEndpoint(awsiotHost, awsiotPort)
myAWSIoTMQTTShadowClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

myAWSIoTMQTTShadowClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTShadowClient.configureConnectDisconnectTimeout(60) # 10sec
myAWSIoTMQTTShadowClient.configureMQTTOperationTimeout(50) #5sec

#connect to AWS IoT
myAWSIoTMQTTShadowClient.connect()

#create a devcie Shadow with persistent subscription
thingName = "my-iot-thing"
deviceShadowHandler = myAWSIoTMQTTShadowClient.createShadowHandlerWithName(thingName, True)

#Delete shadow JSON doc
deviceShadowHandler.shadowDelete(customShadowCallback_delete, 50)

#start a thread to get device status every 5 seconds
statusLoopThread = threading.Thread(target=getDeviceStatus)
statusLoopThread.start()

# Light setting
b = [0, 0, 255]
o = [255, 165, 0]
w = [255,255,255]
z = [0, 0, 0]

initImage = [
o,o,o,o,o,o,o,o,
z,z,z,z,z,z,z,z,
z,z,z,z,z,z,z,z,
z,z,z,z,z,z,z,z,
z,z,z,z,z,z,z,z,
z,z,z,z,z,z,z,z,
z,z,z,z,z,z,z,z,
z,z,z,z,z,z,z,z,
]
sense.set_pixels(initImage)

#update shadow in a loop
deisredTemp = str(35)
desiredHum = str(60)
print("To set desired temperature to " + deisredTemp + "and desired humidity to " + desiredHum+ "\n")
jsonPayload = {"state":{"desired":{"temperature":deisredTemp, "humidity":desiredHum}}}
print("payload is: " + str(jsonPayload) + "\n")
deviceShadowHandler.shadowUpdate(json.dumps(jsonPayload), customShadowCallback_upate, 60)
    