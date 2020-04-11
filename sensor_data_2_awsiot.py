from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
import time
import json
from sense_hat import SenseHat
 
# For certificate based connection
myShadowClient = AWSIoTMQTTShadowClient("my-iot-thing")
# It can be same as the Thing’s name “my-iot-thing” we created above
# For Websocket connection
# myMQTTClient = AWSIoTMQTTClient("myClientID", useWebsocket=True)
# Configurations
# For TLS mutual authentication
myShadowClient.configureEndpoint("a1eeyktzyeh5hs-ats.iot.us-east-1.amazonaws.com", 443)
# The Endpoint can be found in the Interact part in the details of your Thing which showed above
# For Websocket
# myShadowClient.configureEndpoint("YOUR.ENDPOINT", 443)
# For TLS mutual authentication with TLS ALPN extension
# myShadowClient.configureEndpoint("YOUR.ENDPOINT", 443)
myShadowClient.configureCredentials("/home/pi/Scripts/lab3/crt/root-ca-cert.pem","/home/pi/Scripts/lab3/crt/ac354bff74-private.pem.key", "/home/pi/Scripts/lab3/crt/ac354bff74-certificate.pem.crt")
# The three files which we transferred earlier, get the path easily using the method above
# For Websocket, we only need to configure the root CA
# myShadowClient.configureCredentials("YOUR/ROOT/CA/PATH")
myShadowClient.configureConnectDisconnectTimeout(10)  # 10 sec
myShadowClient.configureMQTTOperationTimeout(5)  # 5 sec
 
def customShadowCallback_Update(payload, responseStatus, token):
    # payload is a JSON string ready to be parsed using json.loads(...)
    # in both Py2.x and Py3.x
    if responseStatus == "timeout":
        print("Update request " + token + " time out!")
    if responseStatus == "accepted":
        payloadDict = json.loads(payload)
        print("~~~~~~~~~~~~~~~~~~~~~~~")
        print("Update request with token: " + token + " accepted!")
        print("property: " + str(payloadDict["state"]["reported"]))
        print("~~~~~~~~~~~~~~~~~~~~~~~\n\n")
    if responseStatus == "rejected":
        print("Update request " + token + " rejected!")
 
def customShadowCallback_Delete(payload, responseStatus, token):
    if responseStatus == "timeout":
        print("Delete request " + token + " time out!")
    if responseStatus == "accepted":
        print("~~~~~~~~~~~~~~~~~~~~~~~")
        print("Delete request with token: " + token + " accepted!")
        print("~~~~~~~~~~~~~~~~~~~~~~~\n\n")
    if responseStatus == "rejected":
        print("Delete request " + token + " rejected!")
        
        
myShadowClient.connect()
# Create a device shadow instance using persistent subscription
myDeviceShadow = myShadowClient.createShadowHandlerWithName("my-iot-thing", True)
# The Thing Name is what we created initially, it should be “ my-iot-thing” in the case above
# Delete shadow JSON doc
myDeviceShadow.shadowDelete(customShadowCallback_Delete, 5)
# Shadow operations
 
# This is the shadow message we want to update to the AWS
# NOTE: Don’t put these comment lines into the JSON area
# otherwise it will be wrong and update nothing

# Initialize sense hat
sense = SenseHat()
sense.clear()

temp = sense.get_temperature()
humidity = sense.get_humidity()

temp = round(temp, 1)
humidity = round(humidity, 1)

#get current time
currenttime = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())
# Display humidity and temp readings
print("Moisture Level: {}".format(humidity))
print("Temperature: {}".format(temp))

#level
# ########
raw = sense.accel_raw
x = raw["x"]
y = raw["y"]
z = raw["z"]
print (x,y,z)
level_str = "x: " + str(x) + ", y: " + str(y) + ", z: " + str(z)
orientation = sense.get_orientation_degrees()
print(orientation)
 
JSONPayload = { "state": 
    { "reported":
        { "time":str(currenttime),
          "temperature":str(temp), 
          "humidity":str(humidity),
          "level":level_str
        } 
    }, 
"message": "CDP sensor data"
}
 
# Update shadow JSON
myDeviceShadow.shadowUpdate(json.dumps(JSONPayload), customShadowCallback_Update, 5)
