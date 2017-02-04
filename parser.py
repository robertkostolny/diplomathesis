import pygrib
import numpy as np
from collections import OrderedDict


TURIE = {"lat": 49.85, "lon": 18.16}
RADIUS = 6371000


def potentialToGeometric(altitude):
	result = (altitude*RADIUS)/(RADIUS-altitude)
	return result


def markActiveFields(result, normalizedX, normalizedY, lat, lon):
	x0 = abs(normalizedX - 0.025 - lat)
	x1 = abs(normalizedX + 0.025 - lat)
	y0 = abs(normalizedY - 0.025 - lon)
	y1 = abs(normalizedY + 0.025 - lon)

	if x0 < x1:
		result[-0.05][0.05]['active'] = False
		result[0][0.05]['active'] = False
		result[0.05][0.05]['active'] = False
		direction = -0.05
	else:
		result[-0.05][-0.05]['active'] = False
		result[0][-0.05]['active'] = False
		result[0.05][-0.05]['active'] = False
		direction = 0.05
	if y0 > y1:
		result[-0.05][direction]['active'] = False
		result[-0.05][0]['active'] = False
	else:
		result[0.05][direction]['active'] = False
		result[0.05][0]['active'] = False


def interpolate(start, stop, point, prim, sec):
	result = {}
	metrics = ['altitude', 'pressure', 'temperature']
	result[prim] = point[prim]
	result[sec] = start[sec]
	for metric in metrics:
		interval = stop[metric] - start[metric]
		fraction = abs(point[prim] - start[prim])  / 0.05
		result[metric] = start[metric] + (interval * fraction)
	return result


def parseFile(file_name, lat, lon):
	normalizedX = round(lat * 10 * 2) / 10 /2
	normalizedY = round(lon * 10 * 2) / 10 /2
	station = {'lat': lat, 'lon': lon}
	grbs = pygrib.open(file_name)
	filtered = grbs.select(typeOfLevel='surface')
	result = {
		-0.05: {-0.05: {'active': True}, 0: {'active': True}, 0.05: {'active': True}},
		0: {-0.05: {'active': True}, 0: {'active': True}, 0.05: {'active': True}},
		0.05: {-0.05: {'active': True}, 0: {'active': True}, 0.05: {'active': True}},
	}
	markActiveFields(result, normalizedX, normalizedY, lat, lon)
	for x, row in result.items():
		for y, col in row.items():
			if col['active']:
				for point in filtered:
					if hasattr(point, 'values') and point.values.any():
						if point.parameterName == 'Geopotential height':
							result[x][y]['altitude'] = round(potentialToGeometric(point.values[normalizedX+x][normalizedY+y]), 2)
						if point.parameterName == 'Temperature':
							result[x][y]['temperature'] = round(point.values[normalizedX+x][normalizedY+y], 2)
						if point.parameterName == 'Pressure':
							result[x][y]['pressure'] = round(point.values[normalizedX+x][normalizedY+y], 2)

	selected = {0: {}, 1: {}}
	print '+++++++++++++++++'
	i = -1
	for x, row in result.items():
		prev_i = i
		j = -1
		for y, col in row.items():
			if col['active']:
				j += 1
				if prev_i == i:
					i += 1
				selected[i][j] = {
					'lat': normalizedX + x,
					'lon': normalizedY + y,
					'altitude': col['altitude'],
					'pressure': col['pressure'],
					'temperature': col['temperature']
				}
				print "[%s, %s] - alt: %s, temp: %s, press: %s" % (normalizedX+x, normalizedY+y, col['altitude'], col['temperature'], col['pressure'],  )
	print '+++++++++++++++++'

	M = interpolate(selected[0][0], selected[0][1], station, 'lon', 'lat')	
	N = interpolate(selected[1][0], selected[1][1], station, 'lon', 'lat')
	X = interpolate(M, N, station, 'lat', 'lon')

	print '==================='
	print X


if __name__ == "__main__":
	files = [
		'/home/robko/gfs_4_20130505_1800_120.grb2',
		#'/home/robko/gfs_4_20130505_0000_060.grb2',
		#'/home/robko/gfs_december_sample.grb2'
	]
	for file_name in files:
		parseFile(file_name, TURIE["lat"], TURIE["lon"])
	
