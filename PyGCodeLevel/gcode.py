import helper
import logging
logger = logging.getLogger(__name__)

import re
import numpy as np
import argparse


def match_movement(s):
	"""
		>>> match_movement("X")
		(False, None, None)
		
		>>> match_movement("G01 X1.0500Y-27.8130")
		(True, 'G01', [1.05, -27.813, None])
		
		>>> match_movement("G01 Z-0.2000")
		(True, 'G01', [None, None, -0.2])
		
		>>> match_movement("G00 X39.3197Y-20.3092")
		(True, 'G00', [39.3197, -20.3092, None])
	"""
	m = re.match(r'G0\d', s)
	if not m:
		return (False, None, None)
	g = m.group(0)
	
	r = [None, None, None]
	for axis, value in re.findall(r"([XYZ])([-\d\.]+)", s):
		r[ord(axis) - ord('X')] = float(value)

	return (True, g, r)
		
if __name__ == '__main__':
	helper.logging_config()

def daniel(A, B, C, D, a1, a2, b1, b2):
	"""
		>>> daniel(1, 1, 1, 1, 0.5, 0.5, 0.5, 0.5)
		1.0
		
		>>> daniel(1, 2, 3, 4, 0, 1, 0, 1)
		1.0
		
		>>> daniel(1, 2, 3, 4, 1, 0, 1, 0)
		4.0
	"""
	if a1 + a2 != 1 or b1 + b2 != 1:
		raise Exception("a/b !=1")
		
	return (1.0 - a1) * ((1.0 - b1) * A + (1.0 - b2) * B) \
	     + (1.0 - a2) * ((1.0 - b1) * C + (1.0 - b2) * D)
		
	
def multiplex_files(gcode_filename, heightmap_filename, step_size=5):
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
			
			
			A = hmnp[int(wpos[1] / step_size)][int(wpos[0] / step_size)]
			B = hmnp[int(wpos[1] / step_size)][int(wpos[0] / step_size) + 1]
			C = hmnp[int(wpos[1] / step_size) + 1][int(wpos[0] / step_size)]
			D = hmnp[int(wpos[1] / step_size + 1)][int(wpos[0] / step_size + 1)]
			
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

def gcode_file_info(gcode_filename):
	min_x = 0
	min_y = 0
	max_x = 0
	max_y = 0
	
	# G01 X10Y10Z10
	# G01 X00Y00Z00
	points = []
	points3d = []
	
	with open(gcode_filename, 'r') as gcode_f:
		for line in gcode_f:
			line = line.strip()
			g, success, vector = match_movement(line)
			if success:
				if vector[0] and vector[0] < min_x:
					min_x = vector[0]
				if vector[0] and vector[0] > max_x:
					max_x = vector[0]
					
				if vector[1] and vector[1] < min_y:
					min_y = vector[1]
				if vector[1] and vector[1] > max_y:
					max_y = vector[1]
				
				if vector[0] and vector[1]:
					points.append(vector[:2])
					
				if vector[0] and vector[1] and vector[2] and vector[2] < 0:
					points3d.append(vector)
				
	r = (min_x, min_y, max_x, max_y)
	print("(%s, %s), (%s, %s)" % r)
	# print(points)
	# print(points3d)
	return r
	
if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='GCode Tool')
	parser.add_argument('-g', dest='gcode')
	parser.add_argument('-m', dest='heightmap')
	parser.add_argument('cmd', choices=['info', 'multiplex'])

	args = parser.parse_args()
	# print(args)
	
	if args.cmd == 'info':
		gcode_file_info(args.gcode)
	elif args.cmd == 'multiplex':
		#gcode_file_info(args.gcode)
		multiplex_files(args.gcode, args.heightmap)
	
	# print args.accumulate(args.integers)
	
	# multiplex_files("front.gcode", r"notebooks\hmnp.txt")
	# gcode_file_info("front.gcode")
	
