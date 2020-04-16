# Used to make corresponding actions to raspberry pi
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
import time
import json
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

def customShadowCallback_Get(payload, responseStatus, token):
    print("responseStatus: " + responseStatus)
    print("payload: " + payload)
    payloadDict = json.loads(payload)
    # {"state":{"desired":{"light":37},"delta":{"light":37}},"metadata":{"desired":{"light":{"timestamp":1533888405}}},"version":54
    stateStr = "" 
    try:
        stateStr = stateStr + "Desired: \nTemperature: " + str(payloadDict["state"]["desired"]["temperature"]) + ", "
        stateStr = stateStr + "Humidity: " + str(payloadDict["state"]["desired"]["humidity"])
    except Exception:
        print("No desired state")

    try:
        stateStr = stateStr + "Delta: \nTemperature" + str(payloadDict["state"]["delta"]["temperature"]) + ", "
        stateStr = stateStr + "Humidity" + str(payloadDict["state"]["delta"]["humidity"]) + ", "
        stateStr = stateStr + "Time" + str(payloadDict["state"]["delta"]["timestamp"])
    except Exception:
        print("No delta state")

    try:
        stateStr = stateStr + "Reported: \nTemperature" + str(payloadDict["state"]["reported"]["temperature"]) + ", "
        stateStr = stateStr + "Humidity" + str(payloadDict["state"]["reported"]["humidity"]) + ", "
        stateStr = stateStr + "Level" + str(payloadDict["state"]["reported"]["level"]) + ", "
        stateStr = stateStr + "Time" + str(payloadDict["state"]["reported"]["timestamp"])
    except Exception:
        print("No reported state") 
    
    print(stateStr)

# Light setting
b = [0, 0, 255]
o = [255, 165, 0]
w = [255,255,255]
z = [0, 0, 0]

# create functions to control more lights on or down
def turnUp(image):
    for i in range(0, 32):
        image[i] = o
    return image
    
def turnDown(image):
    for i in range(8, 32):
        image[i] = z
    return image

# create function to stimulate the watering
def water(image):
    for i in range(32, 64):
        image[i] = b
    return image

def customShadowCallback_Delta(payload, responseStatus, token):
    # payload is a JSON string which will be parsed by jason lib
    print(responseStatus)
    print(payload)
    payloadDict = json.loads(payload)
    print("++++++++ Get DELTA data +++++++++++")
    desiredTemp = str(payloadDict["state"]["temperature"])
    desiredHum = str(payloadDict["state"]["humidity"])
    print("desired temperature: " + desiredTemp)
    print("desired humidity: " + desiredHum)
    
    #get device current status
    currentStatus = getDeviceStatus()
    print("Device current status is " + str(currentStatus))
    #udpate device current status
    if currentStatus["temperature"] < float(desiredTemp):
        pixel_list = sense.get_pixels()
        pixel_list = turnUp(pixel_list)
        sense.set_pixels(pixel_list)
    if currentStatus["temperature"] > float(desiredTemp):
        pixel_list = sense.get_pixels()
        pixel_list = turnDown(pixel_list)
        sense.set_pixels(pixel_list)
    if currentStatus["humidity"] < float(desiredHum):
        pixel_list = sense.get_pixels()
        pixel_list = water(pixel_list)
        sense.set_pixels(pixel_list)

    # send current status to IoT service
    sendCurrentState2AWSIoT()
    print("+++++++++++++++++++++++++++\n")

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

sense = SenseHat()

# aws iot info
awsiotHost = "a1eeyktzyeh5hs-ats.iot.us-east-1.amazonaws.com"
awsiotPort = 443;
rootCAPath = "/home/pi/Scripts/lab3/crt/root-ca-cert.pem"
privateKeyPath = "/home/pi/Scripts/lab3/crt/ac354bff74-private.pem.key"
certificatePath = "/home/pi/Scripts/lab3/crt/ac354bff74-certificate.pem.crt"

myAWSIoTMQTTShadowClient = None;
myAWSIoTMQTTShadowClient = AWSIoTMQTTShadowClient("Actuator")
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

#listen on deleta
deviceShadowHandler.shadowRegisterDeltaCallback(customShadowCallback_Delta)

# deviceShadowHandler.shadowGet(customShadowCallback_Get, 60)

while True:
    time.sleep(1)
