import helper
import logging
logger = logging.getLogger(__name__)
import math
from pprint import pprint, pformat
from datetime import datetime
import time, re, sys
import serial
import os
import re
import numpy as np
import argparse
import matplotlib
import matplotlib.pyplot as plt

from gcode import gcode_file_info, match_movement, daniel

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
			
		
if __name__ == '__main__':
	helper.logging_config()

	
def multiplex_files(gcode_filename, bounds, heightmap_filename, step_size=5):
	# G21
	# G90
	# G94
	# F20.00
	# G00 Z10.0000
	# M03 S600
	# G4 P1
	# G00 X1.0500Y-0.1270
	# G01 Z-0.2000
	# G01 X1.0500Y-27.8130
	hmnp = np.loadtxt(heightmap_filename)
	
	wpos = [0, 0]
	wpos_z = 0
	real_z = 0
	line_cnt = 0
	
	with open(gcode_filename, 'r') as gcode_f:
		for line in gcode_f:
			line = line.strip()
			line_cnt += 1
			# if line_cnt > 10:
				# return
			
			# logger.debug(line)
			success, g, vector = match_movement(line)
			if not success:
				print(line)
				continue

			if vector[0]:
				wpos[0] = vector[0]
				
			if vector[1]:
				wpos[1] = vector[1]
				
			if vector[2]:
				wpos_z = vector[2]
				
				
			# logger.debug("(%s, %s), %s" % (wpos[0], wpos[1], wpos_z))
			logger.debug("%s (z:%s)" % (line, wpos_z))

			# real_z = hmnp[int(wpos[1] / step_size)][int(wpos[0] / step_size)]
			# real_z -= hmnp[0][0]
			# real_z = wpos_z + real_z
			
			x = int(math.floor((wpos[0]-bounds[0]) / step_size))
			y = int(math.floor((wpos[1]-bounds[3]) / step_size))
			
			A = hmnp[y][x]
			B = hmnp[y][x + 1]
			C = hmnp[y + 1][x]
			D = hmnp[y + 1][x + 1]
			
			A -= hmnp[0][0]
			B -= hmnp[0][0]
			C -= hmnp[0][0]
			D -= hmnp[0][0]
			
			logger.debug((A, B, C, D))
			
			# logger.debug(wpos[1])
			a1 = (wpos[1] % step_size) / step_size
			b1 = (wpos[0] % step_size) / step_size
			# logger.debug(a1)
			real_z = daniel(A, B, C, D, a1, 1-a1, b1, 1-b1)
			real_z += wpos_z
			
			if vector[0] and vector[1] and not vector[2]:
				print("%s X%.3fY%.3fZ%.3f" % (g, wpos[0], wpos[1], real_z))
			elif not vector[0] and not vector[1] and vector[2]:
				print("%s Z%s" % (g, real_z))
			else:
				#raise Exception("unexpected: %s" % line)
				# G21
				# G90
				# G94
				print(line)

	
def sprint_hmap(hm):
    print ("[ "),
    for idx, row in enumerate(hm):
        if idx > 0:
            print(", "),
        print(row)

    return ("]")
	
def create_height_map(bounds, step_size=5):
	width = bounds[2] - bounds[0] + step_size
	height = bounds[3] - bounds[1] + step_size
	
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
		gcode(s, "G90 G0 X%.3f Y%.3f Z0" % (bounds[0], bounds[3])) # return to zero

		rows = []
		for y in range(int(math.ceil(height / step_size))):
			cols = []
			steps_x = int(math.ceil(width / step_size))
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
	main()
	
def main():
	parser = argparse.ArgumentParser(description='GCode Tool')
	parser.add_argument('-g', dest='gcode')
	parser.add_argument('-s', dest='step_size', type=int, 
						default=5, help='step size')
	parser.add_argument('cmd', choices=['run', 'graph'])

	args = parser.parse_args()
	# print(args)
	
	if args.cmd == 'run':
		# result = create_height_map(**vars(args))
		bounds = gcode_file_info(args.gcode)
		heightmap_filename = args.gcode + '.map'
		if not os.path.isfile(heightmap_filename):
			heightmap = create_height_map(bounds, args.step_size)
			np.savetxt(heightmap_filename, heightmap, '%0.3f')
			
		multiplex_files(args.gcode, bounds, heightmap_filename, args.step_size)
			
	if args.cmd == 'graph':
		heightmap_filename = args.gcode + '.map'
		heightmap = np.loadtxt(heightmap_filename)
		plt.imshow(heightmap)
		plt.colorbar()
		plt.savefig(args.gcode + '.png')

	
	if args.cmd == 'info':
		gcode_file_info(args.gcode)
	
	# print args.accumulate(args.integers)
	
	# multiplex_files("front.gcode", r"notebooks\hmnp.txt")
	# gcode_file_info("front.gcode")
	
