##Code for reading radiation Counts per Minute data of Inspector USB Geiger counter and uploading data to ThingSpeak Data Visualization service##

import paho.mqtt.publish as publish
#import psutil
import usb.core
import usb.util
import time
import sys
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

#Set up logging
log_directory = '/home/pi/logs/radiation.txt'
log_file = open(log_directory, 'a')
log_file.write('Date/time, CPM, CPMmax, CPMavg\n')
log_file.flush()

#look for required usb device (find id from lsusb in command line)
device = None
while device is None:
	device = usb.core.find(idVendor=0x1781, idProduct=0x08e9)
	if device is None:
		sys.stderr.write(str(datetime.datetime.now()) + ': Device not found' + '\n')
		time.sleep(30)

reattach = False
if device.is_kernel_driver_active(0):
	reattach = True
	device.detach_kernel_driver(0)	

# set to current configuration
device.set_configuration()

#read CPM values every 1 second 
#upload average of past 60 values every 60seconds
i = 1
ireset = 60 # How many points to gather before reset 
CPMadd = 0
CPMmax = 0
CPMStatsStr = ',,'
while True:
		
	if i<=ireset:
		unreaddata = True
		while unreaddata:
			try:
				data = device.read(0X81,15)
				unreaddata = False
			except Exception as e:
				sys.stderr.write(str(datetime.datetime.now()) + ': ' + str(e) + '\n')
				usb.util.dispose_resources(device) # Free the USB resource
				device = usb.core.find(idVendor=0x1781, idProduct=0x08e9) # Find the new USB location
				if device.is_kernel_driver_active(0): 
					device.detach_kernel_driver(0) # If it's occupied, free it
				device.set_configuration() # Setup the USB drive to be used again
				time.sleep(30)
				
		time.sleep(1)
		CPM = data[5]
		if CPM>CPMmax:
			CPMmax=CPM
		CPMadd = CPMadd+CPM
		log_file.write(str(datetime.datetime.now()) + ",%d" % CPM + CPMStatsStr + '\n')
		log_file.flush()
		CPMStatsStr = ',,'
		i = i + 1 
	
	else:
		CPMavg = CPMadd/ireset
		CPMStatsStr = ',%d,%d' % (CPMmax, CPMavg)
		dataString = "field1=" + str(CPMavg) + "&field2=" + str(CPMmax)
		
		i = 1
		CPMadd = 0
		CPMmax=0
		#  publish data to channel using parameters for MQTT 
		try:
			publish.single(myChannel, payload=dataString, hostname=mqttHost, port=tPort, tls=tTLS, transport=tTransport)
		except (KeyboardInterrupt):
			break
		except Exception as e:
			sys.stderr.write(str(datetime.datetime.now()) + ": Data was not uploaded - " + str(e) + '\n')
				
log_file.close()
usb.util.dispose_resources(dev)
if reattach:
	device.attach_kernel_driver(0)
