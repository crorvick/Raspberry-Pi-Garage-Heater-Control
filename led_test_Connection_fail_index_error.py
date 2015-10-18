# Scrape the RTRP out of the PJM website
import time, datetime
from lxml import html
import requests
try:
	while True:

		# Use a `Session` instance to customize how `requests` handles making HTTP requests.
		session = requests.Session()
		# `mount` a custom adapter that retries failed connections for HTTP and HTTPS requests.
		session.mount("http://", requests.adapters.HTTPAdapter(max_retries=1))
		#session.mount("https://", requests.adapters.HTTPAdapter(max_retries=1))
		# Rejoice with new fault tolerant behaviour!
		page = session.get(url="http://www.pjm.com/pub/account/lmpgen/lmppost.html")
		#page = requests.get('http://www.pjm.com/pub/account/lmpgen/lmppost.html')    This line is commented out becuase a Session is being used to handle HTTP requests.
		tree = html.fromstring(page.text)
		dateString = '%Y/%m/%d %H:%M:%S'     			
		iprice = tree.xpath('/html/body/center[4]/table/tr[7]/td[3]/text()') # this looks at the 5 minute weighted avg Locational Marginal Prices (LMP) for the ComEd Zone 
		# print iprice
		# this converts the list of one string to a floating point number to allow the adjustments per the tariff filed with the Illinois Commerce Commission on January 14, 2008, these factors are UF = 1.0007 and DLF = 0.0507.
		try:
			number = float(iprice[0]) 
		except IndexError:  #added to skip IndexError errors if encountered
			pass
		# print number
		comed_price = number / 10 * 1.0007 * (1+0.0507) # convert LMP ($/MWhr) to cents/kWhr
		low = 0. #price in cents/kWHr to force the heaters ON
		normal = 0 #price in cents/kWhr to allow the heater t-stat to control
		high = 3  #price in center/kWHr to force the heaters off
		vhigh = 7 #price in center/kWHr to force the heaters off
		supply_cost = 8  #this is the supply cost + taxes + customer charge + fees, etc
		print ' '
		print 'Low         <', supply_cost, u"\u00A2", '/kWHr', ' BLUE'
		print 'Normal ', normal+supply_cost, 'to', high+supply_cost, '        GREEN'
		print 'High  ', high+supply_cost, 'to', vhigh+supply_cost, '       YELLOW'
		print 'V High     >', vhigh+supply_cost, '          RED'
		print 'ComEd Supply', supply_cost, u"\u00A2", "/kWhr"
		print '5 Min Avg   ', round(comed_price, 2), u"\u00A2", "/kWhr "
		print 'Total Cost ', round(comed_price, 2) + supply_cost, u"\u00A2", "/kWhr"
		print datetime.datetime.now().strftime(dateString)
			#Raspberry Pi Control       Web site with info ->  http://www.raspberrypi.org/documentation/usage/python/more.md
		import RPi.GPIO as GPIO
		GPIO.setmode(GPIO.BCM)  #set board mode to Broadcom    # this is an old command for reference only -> GPIO.setmode(GPIO.BOARD)
		GPIO.setwarnings(False)
		GPIO.setup(12, GPIO.OUT) #set up pin 12 for trigger on relay
		#GPIO.setup(16, GPIO.OUT) #set up pin 16 for cancel trigger on Art Controller
		GPIO.setup(19, GPIO.OUT)  #set up pin 19   Control Relay 2 (R2)  GREEN LED
		GPIO.setup(26, GPIO.OUT)  #set up pin 26   Control Relay 1 (R1) This is the t-stat bypass relay curcuit  BLUE LED
		GPIO.setup(13, GPIO.OUT)  #set up pin 13   Yellow LED on (high $/kWHr alert)  RED LED
		GPIO.setup(6, GPIO.OUT)  #setup GPIO pin 6 for Red LED
			#GPIO.cleanup()
			#FOR TESTING          #print 'comed_price = 7'      #comed_price = 7
		if comed_price >= vhigh  :
			GPIO.output(26, 0) #BLUE LED off   Relay 1 off These conditions force the heater OFF
			GPIO.output(19, 0) #GREEN LED off  Relay 2 off
			GPIO.output(13, 0) #YELLOW LED off
			GPIO.output(6, 1) #RED LED on  V High power cost alert
			GPIO.output(12, 1) #relay trigger on
		elif comed_price < vhigh and comed_price >= high :
			GPIO.output(26, 0) #BLUE LED off   Relay 1 off
			GPIO.output(19, 0) #GREEN LED off  Relay 2 off
			GPIO.output(13, 1) #YELLOW LED on
			GPIO.output(6, 0) #RED LED off
			GPIO.output(12, 1) #relay trigger on
		elif comed_price < high and comed_price >= normal :
			GPIO.output(26, 0) #BLUE LED off   Relay 1 off                 
			GPIO.output(19, 1) #GREEN LED on   Relay 2 on
			GPIO.output(13, 0) #YELLOW LED off
			GPIO.output(6, 0) #RED LED off
			GPIO.output(12, 0) #relay trigger off
			    #GPIO.output(16, 1) #cancel trigger on Art Controller 
		else:	
			GPIO.output(26, 1) #BLUE LED on.   Relay 1 on.  These conditions force the heater ON
			GPIO.output(19, 1) #GREEN LED on.  Relay 2 on.
			GPIO.output(13, 0) #YELLOW LED off.
			GPIO.output(6, 0) #RED LED off. 
			GPIO.output(12, 0) #relay trigger off
			    #GPIO.output(16, 1) #cancel trigger on Art Controller
			    # Helpful commands             while true; do sudo python led_test.py; sleep 300; done
		time.sleep (600)
except KeyboardInterrupt:
	pass
GPIO.output(26, 0)
GPIO.output(19, 0)
GPIO.output(13, 0)
GPIO.output(6, 0)
GPIO.output(12, 0)
