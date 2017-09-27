##Code for reading radiation Counts per Minute data of Inspector USB Geiger counter and uploading data to ThingSpeak Data Visualization service##

import paho.mqtt.publish as publish
#import psutil
import usb.core
import usb.util
import time
import datetime
  
#Set channel Identification
# ID = "264331"
# Key = "NCBCW09Y7I1RJM3A"

ID = "332852"
Key = "CP7KTK15VEUHL7UG"
myChannel = "channels/" + ID + "/publish/" + Key

#ThingSpeak MQTT domain
mqttHost = "mqtt.thingspeak.com"
tTransport = "tcp"
tPort = 1883
tTLS = None


#look for required usb device (find id from lsusb in command line)
device = usb.core.find(idVendor=0x1781, idProduct=0x08e9)

if device is None:
    raise ValueError('Device not found')

reattach = False
if device.is_kernel_driver_active(0):
    reattach = True
    device.detach_kernel_driver(0)	

# set to current configuration
device.set_configuration()


#read CPM values every 1 second 
#upload average of past 60 values every 60seconds
i = 1
ireset = 15
CPMadd = 0
CPMmax = 0
while True:
	
	if i<=ireset:
		data = device.read(0X81,15)
		CPM = data[5]
		if CPM>CPMmax:
                    CPMmax=CPM                    
		time.sleep(1)
		CPMadd = CPMadd+CPM
		#print("CPMadd=",CPMadd)
		print(str(datetime.datetime.now()) + ": CPM=",CPM)
		#print("i = ",i)
		i = i +1 
	

	else:
                CPMavg = CPMadd/ireset
		print(str(datetime.datetime.now()) + ": CPMavg=",CPMavg)
		print(str(datetime.datetime.now()) + ": CPMmax=",CPMmax)
		dataString = "field1=" + str(CPMavg) + "&field2=" + str(CPMmax)
		
		i = 1
		CPMadd = 0
		CPMmax=0
    		#  publish data to channel using parameters for MQTT 
    		try:
				publish.single(myChannel, payload=dataString, hostname=mqttHost, port=tPort, tls=tTLS, transport=tTransport)
		except (KeyboardInterrupt):
        		break
		except:
        		print (str(datetime.datetime.now()) + ": Data was not uploaded.")
                
usb.util.dispose_resources(dev)

if reattach:
    device.attach_kernel_driver(0)
