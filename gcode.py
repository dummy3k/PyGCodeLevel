import helper
import logging
logger = logging.getLogger(__name__)

import re
import numpy as np

# G01 Z-0.2000
# G01 X1.0500Y-27.8130
MOVE_REGEX = r""


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
	m = re.match(r'G\d+', s)
	if not m:
		return (False, None, None)
	g = m.group(0)
	
	r = [None, None, None]
	for axis, value in re.findall(r"([XYZ])([-\d\.]+)", s):
		r[ord(axis) - ord('X')] = float(value)

	return (True, g, r)
		
if __name__ == '__main__':
	helper.logging_config()


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
	
	with open(gcode_filename, 'r') as gcode_f:
		for line in gcode_f:
			line = line.strip()
			
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

			real_z = hmnp[int(wpos[1] / step_size)][int(wpos[0] / step_size)]
			real_z -= hmnp[0][0]
			real_z = wpos_z + real_z
			
			if vector[0] and vector[1] and not vector[2]:
				print("%s X%sY%sZ%s" % (g, wpos[0], wpos[1], real_z))
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
				
	r = (min_x, min_y, max_x, max_y)
	print("(%s, %s), (%s, %s)" % r)
	return r
	
if __name__ == '__main__':
	multiplex_files("front.gcode", r"notebooks\hmnp.txt")
	gcode_file_info("front.gcode")
	
