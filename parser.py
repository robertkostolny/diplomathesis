from __future__ import division
import pygrib
import os.path



INPUT_PATH = '/home/robko/grib_data/'
OUTPUT_PATH = '/home/robko/diplomathesis/output/'
DAYS = ["20130530"]
LOOPS = ["0000", "0600", "1200", "1800"]
HOURS = ["000", "033", "063", "096", "129", "159"]
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

# funkcia ktora vybera styri bunky potrebne na interpolaciu z deviatich
def markActiveFields(result, normalizedX, normalizedY, lat, lon):
	x0 = abs(normalizedX - 0.25 - lat) # je vzdialenost od spodnej strany bunky
	x1 = abs(normalizedX + 0.25 - lat) # je vzdialenost od vrchnej strany bunky
	y0 = abs(normalizedY - 0.25 - lon) # je vzdialenost od lavej bunky
	y1 = abs(normalizedY + 0.25 - lon) # je vzdialenost od pravej bunky

	
	if y0 < y1: # pokial vzdialenost od lavej je vacsia ako od pravej tak ma spodok nezaujima (neberiem do uvahy spodne bunky)
		result[-0.5][0.5]['active'] = False
		result[0][0.5]['active'] = False
		result[0.5][0.5]['active'] = False
		direction = -0.5 # bez ohladu na to ci budem mazat pravu alebo lavu stranu tak ymayem stred a vrch
	else:
		result[-0.5][-0.5]['active'] = False
		result[0][-0.5]['active'] = False
		result[0.5][-0.5]['active'] = False
		direction = 0.5
	if x0 > x1: # ci vzdialenost od lavej strany bunky je vacsia ako vzdialenost od pravej strany bunky
		result[-0.5][direction]['active'] = False #zmaze sa vrch(pripadne spodok) podla toho ci v predoslom kroku 
		result[-0.5][0]['active'] = False # zmaze sa stred
	else:
		result[0.5][direction]['active'] = False
		result[0.5][0]['active'] = False

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


def normalize(number):
	normalized = round(number * 4) / 4 # normalizacia suradnice, aby bolo za desatinnou ciarkou suradnice bud 0, 0.25, 0.5 alebo 0.75
	remainder = normalized * 100 % 100 # ulozim si desatinnu cast suradnice
     # pokial je desatinna cast 0.25 alebo 0.75 podmienky sa nevykonanju
	if remainder == 0: #
		if number >= normalized:
			normalized = float(int(normalized)) + 0.25 # priklad: vrati 5.25 ked povodne bolo napr.5.16(interval 5.0 az 5.25), to znamena ze ak je povodne cislo(5.16) vecsie alebo rovne normalizovanemu 5.0 tak odreze od 5.16 desatinne miesta a pricita 0.25 (z cisla 5.16 sa potom stane 5.25)
		else:
			normalized = float(int(number)) + 0.75 #priklad: vrati 4.75 ked povodne bolo napr. 4.91(interval 4.75 az 5.0), postup taky isty ako v predoslom komentari len nepricita 0.25 ale 0.75.
	elif remainder == 50:
		if number >= normalized:
			normalized = float(int(normalized)) + 0.75 # to iste len pre iny interval hodnot
		else:
			normalized = float(int(number)) + 0.25
	return normalized

# parsovanie dat zo suborov GFS
def parseFile(station_name, file_name, lat, lon):
	normalizedX = normalize(lat) 
	normalizedY = normalize(lon)
	station = {'lat': lat, 'lon': lon}
	if not os.path.isfile(file_name): 
		return False
	grbs = pygrib.open(file_name)
	filtered = grbs.select(typeOfLevel='surface') # surface je nazov hladiny z ktorej boli metriky (veliciny) parsovane
     # dvojzrozmerne pole 3x3 bunky a v strede je bunka kde lezi stanica
	result = {
		-0.5: {-0.5: {'active': True}, 0: {'active': True}, 0.5: {'active': True}}, # slovnik kde klucom je posun (-0.5, 0, 0.5)
		0: {-0.5: {'active': True}, 0: {'active': True}, 0.5: {'active': True}},
		0.5: {-0.5: {'active': True}, 0: {'active': True}, 0.5: {'active': True}},
	}
	markActiveFields(result, normalizedX, normalizedY, lat, lon)
	for x, row in result.items(): # prechadza aktivne riadky z vybranych deviatich
		for y, col in row.items(): # prechadza aktivne stlpce z vybranych deviatich
			if col['active']: 
				for metric_value in filtered: # vyber hodnoty veliciny z hladiny surface
					if hasattr(metric_value, 'values') and metric_value.values.any():
                                 # x,y je posun na zaklade ktoreho je vkladana hodnota tlaku, tepoty a vysky do resultu
						if metric_value.parameterName == 'Geopotential height':
							result[x][y]['altitude'] = round(potentialToGeometric(metric_value.values[normalizedX+x][normalizedY+y]), 2)
						if metric_value.parameterName == 'Temperature':
							result[x][y]['temperature'] = round(metric_value.values[normalizedX+x][normalizedY+y], 2)
						if metric_value.parameterName == 'Pressure':
							result[x][y]['pressure'] = round(metric_value.values[normalizedX+x][normalizedY+y], 2)
	selected = {0: {}, 1: {}} #
	# print '+++++++++++++++++'
	i = -1
	# print "-- %s  --" % (station_name)
     # nutne aby sa vybrane 4 bunky nepoprehadzovali ked sa budu ukladat do novej matice 2x2 (aby bolo zachovane poradie stlcpov a riadkov ako v povovdnej matici 3x3 - kvoli interpolaci)
	for x, row in result.items(): # prechadzam riadky resultu (mam 9 zaznamov a z toho mam hodnoty iba pri styroch aktivnych)
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
				# print "[%s, %s] - alt: %s, temp: %s, press: %s" % (normalizedX+x, normalizedY+y, col['altitude'], col['temperature'], col['pressure'],  )
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
    #interpolacia
	M = interpolate(selected[0][0], selected[0][1], station, 'lon', 'lat')	
	N = interpolate(selected[1][0], selected[1][1], station, 'lon', 'lat')
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

