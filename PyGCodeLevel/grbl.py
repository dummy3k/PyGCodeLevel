#!/usr/bin/env python

import serial
import time, re, sys
import helper
from pprint import pprint, pformat
from datetime import datetime
import numpy as np
import argparse

import logging
logger = logging.getLogger(__name__)

short_sleep = 0.1
long_sleep = 1

def gcode(s, cmd):
	logger.debug(">>> %s" % cmd)
	s.write(cmd + '\n')
	s.flushInput()

	grbl_out = None
	while grbl_out != 'ok':
		# s.write('?' + '\n')
		time.sleep(short_sleep)
		grbl_out = s.readline().strip()
		# logger.debug("<<< %s" % grbl_out),

	logger.debug(grbl_out)
	return grbl_out

def status(ser):
	cmd = "?"
	logger.debug(">>> %s" % cmd)
	ser.write(cmd + '\n')
	ser.flushInput()

	result = ser.readline().strip()
	logger.debug(result)
	# result = gcode(ser, "?")
	if result == "ok":
		return (result, )

	p = r"<(\w+),MPos:([-\d\.]+),([-\d\.]+),([-\d\.]+),WPos:([-\d\.]+),([-\d\.]+),([-\d\.]+)>"
	m = re.match(p, result)
	if not m:
		p = r"\[PRB:([-\d\.]+),([-\d\.]+),([-\d\.]+):([-\d\.]+)]"
	m = re.match(p, result)

	return m.groups()

def wait_idle(s):
	while True:
		r = status(s)

		if r[0] == "ok":
			time.sleep(short_sleep)
		elif r[0] == "Run":
			time.sleep(long_sleep)
		else:
			return r

def sprint_hmap(hm):
    print ("[ "),
    for idx, row in enumerate(hm):
        if idx > 0:
            print(", "),
        print(row)

    return ("]")
	
def create_height_map(width, height, step_size=5):
	start_time = datetime.now()
	with serial.Serial("COM5", 115200) as s:
		s.timeout = 3

		# Wake up grbl
		s.write("\r\n\r\n")
		time.sleep(2)   # Wait for grbl to initialize
		s.flushInput()  # Flush startup text in serial input

		gcode(s, "$H")
		gcode(s, "G10 P0 L20 Z0") 	# reset Z
		logger.info(status(s))
		gcode(s, "G90 G0 X0 Y0 Z0") # return to zero

		rows = []
		for y in range(height / step_size):
			cols = []
			steps_x = width / step_size
			for x in range(steps_x):
				gcode(s, "G38.2 Z-26 F100")	#probe
				gcode(s, "G91 G0 Z0.4")
				gcode(s, "G38.2 Z-26 F10")	#probe
				
				current_status = status(s)
				logger.debug(current_status)
				
				z = float(current_status[6])
				logger.info("%s, %s = %s" % (x, y, z))
				if y % 2 == 0:
					cols.append(z)
				else:
					cols.insert(0, z)
				
				gcode(s, "G91 G0 Z1")
				if x + 1 == steps_x:
					# dont move at the end
					pass
				elif y % 2 == 0:
					gcode(s, "G91 G0 X%i" % step_size)
				else:
					gcode(s, "G91 G0 X-%i" % step_size)

			rows.append(cols)
			logger.info(pformat(cols))
			gcode(s, "G91 G0 Y-%i" % step_size)
		
		# logger.info(pformat(rows))
		logger.debug(rows)
		# logger.info(sprint_hmap(rows))
		gcode(s, "G90 G0 X0 Y0 Z0") # return to zero
	
	end_time = datetime.now()
	logger.info("duration: %s" % (end_time - start_time))
	return rows
	
	# np.savetxt('hmnp.txt', rows, '%.3f')

	
if __name__ == '__main__':
	helper.logging_config()
	
	parser = argparse.ArgumentParser(description='Create heightmap',
									 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	# parser.add_argument('-g', dest='gcode')
	parser.add_argument('-x', dest='width', type=int)
	parser.add_argument('-y', dest='height', type=int)
	parser.add_argument('-s', dest='step_size', type=int, 
						default=5, help='step size')
	parser.add_argument('-f', dest='file', type=str)
	# parser.add_argument('cmd', choices=['info', 'multiplex'])

	args = parser.parse_args()
	if not args.file:
		print("missing file argument")
		sys.exit(1)
		
	# result = create_height_map(**vars(args))
	result = create_height_map(args.width, args.height, args.step_size)
	# result = [  [-12.558, -12.551, -12.544]
				# ,  [-12.567, -12.56, -12.556]
				# ,  [-12.58, -12.576, -12.559]]
	np.savetxt(args.file, result, '%0.3f')
	