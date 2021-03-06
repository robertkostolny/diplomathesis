from __future__ import division
import pygrib
import os.path
import numpy as np
from collections import OrderedDict


INPUT_PATH = '/home/robko/grib_data/'
OUTPUT_PATH = '/home/robko/diplomathesis/output/'
DAYS = ["20130520"]
LOOPS = ["0000", "0600", "1200", "1800"]
HOURS = ["000", "033", "063", "096", "129", "159"]
STATIONS = {
	'VSBO': {'lat': 49.85, 'lon': 18.16},
	# 'PLZN': {'lat': 49.73, 'lon': 18.35},
	# 'WTZR': {'lat': 50.08, 'lon': 12.52},
	# 'ZYWI': {'lat': 49.41, 'lon': 19.12},
	# "KUNZ": {"lat": 49.06, "lon": 15.12},
	# "GOPE": {"lat": 49.55, "lon": 14.47},
	# "TUBO": {"lat": 49.12, "lon": 16.35},
	# "VACO": {"lat": 49.08, "lon": 13.43},
	# "BISK": {"lat": 50.15, "lon": 17.25},
	# "DRES": {"lat": 51.01, "lon": 13.43},
	# "KATO": {"lat": 50.15, "lon": 19.02},
	# "MOPI": {"lat": 48.22, "lon": 17.16},
	
}
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
		result[-0.5][0.5]['active'] = False
		result[0][0.5]['active'] = False
		result[0.5][0.5]['active'] = False
		direction = -0.5
	else:
		result[-0.5][-0.5]['active'] = False
		result[0][-0.5]['active'] = False
		result[0.5][-0.5]['active'] = False
		direction = 0.5
	if y0 > y1:
		result[-0.5][direction]['active'] = False
		result[-0.5][0]['active'] = False
	else:
		result[0.5][direction]['active'] = False
		result[0.5][0]['active'] = False


def interpolate(start, stop, point, prim, sec):
	result = {}
	metrics = ['altitude', 'pressure', 'temperature']
	result[prim] = point[prim]
	result[sec] = start[sec]
	for metric in metrics:
		interval = stop[metric] - start[metric]
		fraction = abs(point[prim] - start[prim])  / 0.5
		result[metric] = round(start[metric] + (interval * fraction), 2)
	return result


def normalize(number):
	normalized = round(number * 4) / 4
	remainder = normalized * 100 % 100
	if remainder == 0:
		if number > normalized:
			normalized = float(int(normalized)) + 0.25
		else:
			normalized = float(int(number)) + 0.75
	elif remainder == 50:
		if number > normalized:
			normalized = float(int(normalized)) + 0.75
		else:
			normalized = float(int(number)) + 0.25
	return normalized


def parseFile(file_name, lat, lon):
	normalizedX = normalize(lat)
	normalizedY = normalize(lon)
	station = {'lat': lat, 'lon': lon}
	if not os.path.isfile(file_name):
		return False
	grbs = pygrib.open(file_name)
	# typeOfLevel zmenit na isobaricInhPa
	filtered = grbs.select(typeOfLevel='surface')
	result = {
		-0.5: {-0.5: {'active': True}, 0: {'active': True}, 0.5: {'active': True}},
		0: {-0.5: {'active': True}, 0: {'active': True}, 0.5: {'active': True}},
		0.5: {-0.5: {'active': True}, 0: {'active': True}, 0.5: {'active': True}},
	}
	markActiveFields(result, normalizedX, normalizedY, lat, lon)
	for x, row in result.items():
		for y, col in row.items():
			if col['active']:
				for point in filtered:
					if hasattr(point, 'values') and point.values.any():
						# po zmene na isobaricInhPa nedostanem 1 hodnotu, ale pole hodnot pre kazdy "level" tlaku. Tu si teda ulozim do resultu nie altitude, pressure, temperature ale pole levelov, kde kazdy ma temperature a altitude
						if point.parameterName == 'Geopotential height':
							result[x][y]['altitude'] = round(potentialToGeometric(point.values[normalizedX+x][normalizedY+y]), 2)
						if point.parameterName == 'Temperature':
							result[x][y]['temperature'] = round(point.values[normalizedX+x][normalizedY+y], 2)
						if point.parameterName == 'Pressure':
							result[x][y]['pressure'] = round(point.values[normalizedX+x][normalizedY+y], 2)
	# Tu uz mam 9 poli, ktore obklopuju to, do ktoreho spada stanica. Nadmorsku vysku stanice musim umiestnit do niektoreho z levelov modelu isobaricInhPa. Nasledne pre kazde z 9 poli vyberiem ten zaznam z levels, ktory ma tuto nadmorsku vysku
	# Vysledkom je transformacia z formatu {level -> alt, temp} na format {alt, temp, press} potom uz sa kod sprava ako doteraz
	selected = {0: {}, 1: {}}
	# print '+++++++++++++++++'
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
	return
	# print '+++++++++++++++++'

	# selected = {
	# 	0: {
	# 		0: {'lat': 49.85, 'lon': 18.15, 'altitude': 345, 'pressure': 1024, 'temperature': 273},
	# 		1: {'lat': 49.85, 'lon': 18.2, 'altitude': 339, 'pressure': 1036, 'temperature': 269},
	# 	},
	# 	1: {
	# 		0: {'lat': 49.9, 'lon': 18.15, 'altitude': 340, 'pressure': 1000, 'temperature': 280},
	# 		1: {'lat': 49.9, 'lon': 18.2, 'altitude': 349, 'pressure': 1020, 'temperature': 275},
	# 	}
	# }

	M = interpolate(selected[0][0], selected[0][1], station, 'lon', 'lat')	
	N = interpolate(selected[1][0], selected[1][1], station, 'lon', 'lat')
	X = interpolate(M, N, station, 'lat', 'lon')

	# print '==================='
	# print M
	# print N
	# print X
	return X


def zero(hour):
	if hour == "000":
		return "0000"
	if hour == "033":
		return "0100"
	if hour == "063":
		return "0200"
	if hour == "096":
		return "0300"
	if hour == "129":
		return "0400"
	return "0500"


def six(hour):
	if hour == "000":
		return "0600"
	if hour == "033":
		return "0700"
	if hour == "063":
		return "0800"
	if hour == "096":
		return "0900"
	if hour == "129":
		return "1000"
	return "1100"


def twelve(hour):
	if hour == "000":
		return "1200"
	if hour == "033":
		return "1300"
	if hour == "063":
		return "1400"
	if hour == "096":
		return "1500"
	if hour == "129":
		return "1600"
	return "1700"


def eighteen(hour):
	if hour == "000":
		return "1800"
	if hour == "033":
		return "1900"
	if hour == "063":
		return "2000"
	if hour == "096":
		return "2100"
	if hour == "129":
		return "2200"
	return "2300"	


def getOutputHour(loop, hour):
	if loop == "0000":
		return zero(hour)
	if loop == "0600":
		return six(hour)
	if loop == "1200":
		return twelve(hour)
	return eighteen(hour)


def parseStation(day, station, coords):
	save_name = OUTPUT_PATH + station + day[2:] + '.txt'
	fo = open(save_name, "wb")
	for loop in LOOPS:
		for hour in HOURS:
			file_name = INPUT_PATH + 'gfs_4_' + day + '_' + loop + '_' + hour + '.grb2'
			result = parseFile(file_name, coords['lat'], coords['lon'])
			if result:
				file_line = "%s %s %s %s %s %s" % (station, day[2:], getOutputHour(loop, hour), result['pressure'], result['temperature'], result['altitude'])
				print file_line
				fo.write(file_line + '\n')
	fo.close()


if __name__ == "__main__":
	for day in DAYS:
		for station, coords in STATIONS.items():
			parseStation(day, station, coords)

