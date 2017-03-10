from __future__ import division
from collections import defaultdict
import pygrib
import os.path



INPUT_PATH = '/home/robko/grib_data/'
OUTPUT_PATH = '/home/robko/diplomathesis/output/'
DAYS = ["20130507", "20130508"]
LOOPS = ["0000", "0600", "1200", "1800"]
HOURS = ["006", "009"]
STATIONS = {
	'VSBO': {'lat': 49.85, 'lon': 18.16},
	'PLZN': {'lat': 49.73, 'lon': 18.35},
	'WTZR': {'lat': 50.08, 'lon': 12.52},
	'ZYWI': {'lat': 49.41, 'lon': 19.12},
	"KUNZ": {"lat": 49.06, "lon": 15.12},
	"GOPE": {"lat": 49.55, "lon": 14.47},
	"TUBO": {"lat": 49.12, "lon": 16.35},
	"VACO": {"lat": 49.08, "lon": 13.43},
	"BISK": {"lat": 50.15, "lon": 17.24},
	"DRES": {"lat": 51.01, "lon": 13.43},
	"KATO": {"lat": 50.15, "lon": 19.02},
	"MOPI": {"lat": 48.22, "lon": 17.16},
	
}
RADIUS = 6371000 # polomer Zeme v metroch

# funkcia prepocitava potencialnu vysku modelu na geometricku(nadmorsku)
def potentialToGeometric(altitude):
	result = (altitude*RADIUS)/(RADIUS-altitude)
	return result

# bilinearna interpolacia pre odhad hodnot v mieste stanice
def interpolate(start, stop, point, prim, sec):
	result = {}
	metrics = ['altitude', 'pressure', 'temperature']
	result[prim] = point[prim] # prim - je primarna suradnica (zalezi od toho v ktorom smere sa zacina interpolacia)
	result[sec] = start[sec]
	for metric in metrics:
		interval = stop[metric] - start[metric] # hodnota rozdielu metrik medzi zaciatkom a koncom bunky
		fraction = abs(point[prim] - start[prim])  / 0.5 # o kolko je posunuta stanica od zaciatku intervalu(bunky) a podelim to sirkou bunky (suradnicovy rozdiel)
		result[metric] = round(start[metric] + (interval * fraction), 2) # k hodnote metriky ktora je na zaciatku intervalu pripocitam hodnotu metriky vypocitanu pomocou premennych - interval a fraction
	return result

def getCornerPoints(normalized, station):
	result = defaultdict(lambda: defaultdict(dict))
	normalized['x_lat'] = normalized['lat'] + 0.5
	if station['lat'] < normalized['lat']:
		normalized['x_lat'] = normalized['lat'] - 0.5
	result[normalized['x_lat']] = {}
	result[normalized['lat']] = {}
	normalized['y_lon'] = normalized['lon'] + 0.5
	if station['lon'] < normalized['lon']:
		normalized['y_lon'] = normalized['lon'] - 0.5
	for i in ('lat', 'x_lat',):
		result[normalized[i]][normalized['lon']] = {'lat': normalized[i], 'lon': normalized['lon']}
		result[normalized[i]][normalized['y_lon']] = {'lat': normalized[i], 'lon': normalized['y_lon']}
	return result, normalized['lat'], normalized['x_lat'], normalized['lon'], normalized['y_lon']

# parsovanie dat zo suborov GFS
def parseFile(station_name, file_name, lat, lon):
	normalizedX = round(lat * 2) / 2
	normalizedY = round(lon * 2) / 2
	station = {'lat': lat, 'lon': lon}
	normalized = {'lat': normalizedX, 'lon': normalizedY}
	if not os.path.isfile(file_name): 
		return False
	grbs = pygrib.open(file_name)
	filtered = grbs.select(typeOfLevel='surface') # surface je nazov hladiny z ktorej boli metriky (veliciny) parsovane
	
	print 'STATION: %s, LAT: %s, LON: %s, NORMALIZED_LAT: %s, NORMALIZED_LON: %s' % (station_name, lat, lon, normalizedX, normalizedY)
	(result, x1, x2, y1, y2) = getCornerPoints(normalized, station)
	for x, row in result.items(): # prechadza aktivne riadky z vybranych deviatich
		for y, col in row.items(): # prechadza aktivne stlpce z vybranych deviatich
			print 'LAT: %s, LON: %s' % (x, y)
			for metric_value in filtered: # vyber hodnoty veliciny z hladiny surface
				if hasattr(metric_value, 'values') and metric_value.values.any():
                                 	# x,y je posun na zaklade ktoreho je vkladana hodnota tlaku, tepoty a vysky do resultu
					if metric_value.parameterName == 'Geopotential height':
						result[x][y]['altitude'] = round(potentialToGeometric(metric_value.values[x][y]), 2)
					if metric_value.parameterName == 'Temperature':
						result[x][y]['temperature'] = round(metric_value.values[x][y], 2)
					if metric_value.parameterName == 'Pressure':
						result[x][y]['pressure'] = round(metric_value.values[x][y], 2)
				
    #interpolacia
	M = interpolate(result[x1][y1], result[x1][y2], station, 'lon', 'lat')	
	N = interpolate(result[x2][y1], result[x2][y2], station, 'lon', 'lat')
	X = interpolate(M, N, station, 'lat', 'lon')

	# print '==================='
	# print M
	# print N
	# print X
	return X

# definovanie casovej stopy vstupnych suborov
def zero(hour):
	if hour == "006":
		return "0600"
	return "0900"

def six(hour):
	if hour == "006":
		return "1200"
	return "1500"

def twelve(hour):
	if hour == "006":
		return "1800"
	return "2100"

def eighteen(hour):
	if hour == "006":
		return "2400"
	return "0300"	


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
			result = parseFile(station, file_name, coords['lat'], coords['lon'])
			if result:
				file_line = "%s %s %s %s %s %s" % (station, day, getOutputHour(loop, hour), result['pressure'], result['temperature'], result['altitude'])
				print file_line
				fo.write(file_line + '\n')
	fo.close()


if __name__ == "__main__":
	for day in DAYS:
		for station, coords in STATIONS.items(): 
			parseStation(day, station, coords) # zavolanie stanice so suradnicami pre konkretny den

