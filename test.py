#!/usr/bin/env python
"""\
Simple g-code streaming script for grbl
"""
 
import serial
import time, re

def gcode(s, cmd):
	print(">>> %s" % cmd)
	s.write(cmd + '\n')
	grbl_out = s.readline()
	print("<<< %s" % grbl_out)
	return grbl_out
	
def status(ser):
	p = r"<(\w+),MPos:([-\d\.]+),([-\d\.]+),([-\d\.]+),WPos:([-\d\.]+),([-\d\.]+),([-\d\.]+)>"
	result = gcode(ser, "?")
	if result.strip() == "ok":
		return (result.strip(), )
		
	m = re.match(p, result)
	if not m:
		p = r"\[PRB:([-\d\.]+),([-\d\.]+),([-\d\.]+):([-\d\.]+)]"
	m = re.match(p, result)
	
	return m.groups()

def wait_idle(s):
	short_sleep = 0.1
	long_sleep = 1
	while True:
		r = status(s)
		
		if r[0] == "ok":
			time.sleep(short_sleep)
		elif r[0] == "Run":
			time.sleep(long_sleep)
		else:
			return r
	
with serial.Serial("COM5", 115200) as s:
	s.timeout = 3

	# Wake up grbl
	s.write("\r\n\r\n")
	time.sleep(2)   # Wait for grbl to initialize
	s.flushInput()  # Flush startup text in serial input
	
	gcode(s, "$H") 
	# # gcode(s, "G90 G0 X0 Y0 Z0")	#return to zero
	# gcode(s, "G91 G0 Z5")		#rel. up +5Z
	# # wait_idle(s)
	
	# for x in range(5):
		# gcode(s, "G38.2 Z-26 F100")	#probe
		# wait_idle(s)
		# print("**********")
		# print(wait_idle(s))
		# print("**********")
		
		# gcode(s, "G91 G0 Z1")
		# wait_idle(s)

		# gcode(s, "G91 G0 X1")
		# wait_idle(s)

	
# Open grbl serial port
# s = serial.Serial('COM5',115200)

 
def send_gcode_file(): 
	# Open g-code file
	f = open('somefile.gcode','r');
	 
	 
	# Stream g-code to grbl
	for line in f:
		l = line.strip() # Strip all EOL characters for streaming
		print 'Sending: ' + l,
		s.write(l + '\n') # Send g-code block to grbl
		grbl_out = s.readline() # Wait for grbl response with carriage return
		print ' : ' + grbl_out.strip()
	 
	# Wait here until grbl is finished to close serial port and file.
	raw_input("  Press <Enter> to exit and disable grbl.")
 
	# Close file and serial port
	f.close()
	
# s.close()


