import pygrib
import numpy as np
from collections import OrderedDict


TURIE = {"lat": 49.81, "lon": 18.17}
RADIUS = 6371000


def potentialToGeometric(altitude):
	result = (altitude*RADIUS)/(RADIUS-altitude)
	return result


def markActiveFields(result, lat, lon):
	normalizedX = round(lat * 10 * 2) / 10 /2
	normalizedY = round(lon * 10 * 2) / 10 /2
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
	if y0 < y1:
		result[-0.05][direction]['active'] = False
		result[-0.05][0]['active'] = False
	else:
		result[0.05][direction]['active'] = False
		result[0.05][0]['active'] = False

def parseFile(file_name, lat, lon):
	grbs = pygrib.open(file_name)
	filtered = grbs.select(typeOfLevel='surface')
	result = {
		-0.05: {-0.05: {'active': True}, 0: {'active': True}, 0.05: {'active': True}},
		0: {-0.05: {'active': True}, 0: {'active': True}, 0.05: {'active': True}},
		0.05: {-0.05: {'active': True}, 0: {'active': True}, 0.05: {'active': True}},
	}
	markActiveFields(result, lat, lon)
	for x, row in result.items():
		for y, col in row.items():
			for point in filtered:
				if hasattr(point, 'values') and point.values.any():
					if point.parameterName == 'Geopotential height':
						result[x][y]['altitude'] = round(potentialToGeometric(point.values[lat+x][lon+y]), 2)
					if point.parameterName == 'Temperature':
						result[x][y]['temperature'] = round(point.values[lat+x][lon+y], 2)
					if point.parameterName == 'Pressure':
						result[x][y]['pressure'] = round(point.values[lat+x][lon+y], 2)

	print '+++++++++++++++++'
	for x, row in result.items():
		for y, col in result[x].items():
			if col['active']
			print "[%s, %s] - alt: %s, temp: %s, press: %s" % (lat+x, lon+y, col['altitude'], col['temperature'], col['pressure'],  )
	print '+++++++++++++++++'


if __name__ == "__main__":
	files = [
		'/home/robko/gfs_4_20130505_1800_120.grb2',
		#'/home/robko/gfs_4_20130505_0000_060.grb2',
		#'/home/robko/gfs_december_sample.grb2'
	]
	for file_name in files:
		parseFile(file_name, TURIE["lat"], TURIE["lon"])
	
