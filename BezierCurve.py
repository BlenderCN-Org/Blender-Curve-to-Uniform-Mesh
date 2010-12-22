# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
import mathutils
from mathutils import Vector
from blender_curve_to_mesh.BezierSegmentIterator import *
from math import *

class BezierCurve:
	# Vector which holds the control points of the curve
	# each 3*n element is a vertex, and the others are control
	# points
	controlPoints = []

	def segmentCount(self):
		return len(self.controlPoints) // 3

	# Returns a point in the array
	def pointAtIdx(self, index):
		# Make sure to clip the index values
		while (index < 0):
			index += len(self.controlPoints)
		index %= len(self.controlPoints)
		return self.controlPoints[index].copy()

	# Returns a control point of a specified segment
	# if id = 0, it returns the start vertex
	#    id = 1 or 2, the first and second control point
	# if id = 3, the end vertex
	def pointAt(self, segment, idx):
		return self.pointAtIdx(segment * 3 + idx)

	# Appends a segment to the bezier curve, specifing the start
	# vertex, and the two control points
	def appendSegment(self, s, v1, v2):
		self.controlPoints.append(s.copy())
		self.controlPoints.append(v1.copy())
		self.controlPoints.append(v2.copy())

	# Returns an BezierSegmentIterator instance, useful to iterate
	# trough the segments
	def getIterator(self, idx):
		return BezierSegmentIterator(self, idx)

	# Turns the bezier curve into a list of coordinates, which can be
	# connected to form an edge loop
	def toPointCloud(self, firstPassResolution, density):
		points = []

		if self.segmentCount() == 0:
			return points

		iterator = self.getIterator(0)
		while True:

			count = round(iterator.computeLength(firstPassResolution) * density)
			count = max(1, count)
			print("count = " + str(count))

			for j in range(0, count):
				t = float(j) / count
				print("t = " + str(t))
				points.append(iterator.pointAt(t))

			if not iterator.next():
				break

		return points

	# Turns the offsetted bezier curve into a list of coordinates
	# Which can easly be transformed into an edge loop
	def toOfsettedPointCloud(self, offset, firstPassResolution, density):
		points = []

		it = self.getIterator(0)
		itN = self.getIterator(1)

		while True:

			count = round(it.computeLength(firstPassResolution) * density)
			count = max(1, count)
			print("count = " + str(count))

			# We have to include also the last vertex (as it is
			# offsetted anyway!
			for j in range(0, count + 1):
				t = float(j) / count
				co = it.pointAt(t)
				no = it.normalAt(t)
				points.append(co + (no * offset))

				p1 = it.pointAt(1) + it.normalAt(1) * offset
				p2 = itN.pointAt(0) + itN.normalAt(0) * offset
				p1 = it.pointAt(1) + it.normalAt(1) * offset
			if(False): # use straight segments to connect the vertices
				# Calculate intersection between the offsetted tangents of two adiacent points,
				# and add that point
				#v1 = it.tangentAt(1)
				#v2 = itN.tangentAt(0)
				#pn = (LineLineIntersect(p1, p1 + v1, p2, p2 + v2))
				#if pn != None:
				#	points.append(p1)
				pass
			else: # use arcs to connect the vertices
				v1 = it.normalAt(1)
				v2 = itN.normalAt(0)
				#alpha = acos(v2.dot(v1))
				alpha = GetAngle(v1)
				beta = GetAngle(v2)
				delta = beta - alpha
				# Normalize the delta
				if(delta > pi):
					delta -= 2 * pi
				if(delta < -pi):
					delta += 2 * pi
				print(">>>alpha = " + str(alpha/pi*180))
				print(">>>beta  = " + str(beta/pi*180))
				print(">>>delta = " + str(delta/pi*180))
				if(True or delta > -pi and delta < 0): # in this case flip the delta
					center = it.pointAt(1)
					for i in range(1,10):
						points.append(Vector((cos(alpha + delta * i / 10), sin(alpha + delta * i / 10), 0)) * offset + center)

			if not it.next():
				break
			itN.next()
		return points

def LineLineIntersect (p1, p2, p3, p4):
	# based on Paul Bourke's Shortest Line Between 2 lines

	min = 0.0000001
	v1 = p1 - p3 #Vector((p1.x - p3.x, p1.y - p3.y, p1.z - p3.z))
	v2 = p4 - p3 #Vector((p4.x - p3.x, p4.y - p3.y, p4.z - p3.z))

	if abs(v2.x) < min and abs(v2.y) < min and abs(v2.z) < min:
		return None

	v3 = p2 - p1

	if abs(v3.x) < min and abs(v3.y) < min and abs(v3.z) < min:
		return None

	d1 = v1.dot(v2)
	d2 = v2.dot(v)
	d3 = v1.dot(v3)
	d4 = v2.dot(v2)
	d5 = v3.dot(v3)
	d = d5 * d4 - d2 * d2

	if abs(d) < min:
		return None

	n = d1 * d2 - d3 * d4
	mua = n / d
	mub = (d1 + d2 * (mua)) / d4

	# Return the center of the two evaluated points
	return ((p1 + mua * v3) + (p3  + mub * v2)) / 2
	#ua = (p4.x - p3.x) * (p1.y - p3.y) - (p4.y - p3.y) * (p1.x - p3.x) /
	#	((p4.y - p3.y) * (p2.x - p1.x) - (p4.x - p3.x) * (p2.y - p1.y))
	#
	#return p1 + (p2 - p1) * ua

def GetAngle(v):
	# returns theta in interval [-pi, pi]
	if v.x > 0:
		theta = atan(v.y / v.x)
	elif v.x < 0 and v.y >= 0:
		theta = atan(v.y / v.x) + pi
	elif v.x < 0 and v.y < 0:
		theta = atan(v.y / v.x) - pi
	elif v.x == 0 and v.y > 0:
		theta = pi / 2
	elif v.x == 0 and v.y < 0:
		theta = -pi / 2
	else:
		theta = 0

	return theta
