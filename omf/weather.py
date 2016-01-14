# Portions Copyright (C) 2015 Intel Corporation
''' weather.py pulls weather data from wunderground.com, and formats it as a CSV that
can be input to a Gridlab-D Climate object.

For example, to get a CSV that will play back 1 month of weather data
for the region near the DCA airport, run in the terminal:

	python -c "import weather; weather.makeClimateCsv('2010-07-01', '2010-08-01', 'DCA', './weatherDCA.csv')"

To use that data as the climate simulation in a Gridlab model, include
the following in a .glm:

	module tape;
	module climate;

	object csv_reader {
		name "weatherReader";
		filename "weatherDCA.csv";
	};

	object climate {
		name "exampleClimate";
		tmyfile "weatherDCA.csv";
		reader weatherReader;
	}
'''

import os
import urllib
import csv
import math
import re
import tempfile
import shutil
import urllib2
import sys
from os.path import join as pJoin
from datetime import timedelta, datetime
from math import modf
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


def makeClimateCsv(start, end, airport, outFilePath, cleanup=True):
    ''' Generate a climate timeseries CSV. See module docString for full help.'''
    tempDir = tempfile.mkdtemp()
    print "Working in", tempDir
    _downloadWeather(start, end, airport, tempDir)
    _getPeakSolar(airport, tempDir)
    _processWeather(start, end, airport, tempDir)
    shutil.copyfile(pJoin(tempDir, "weather.csv"), outFilePath)
    print "Output CSV available at", outFilePath
    if cleanup:
        shutil.rmtree(tempDir)
        print "Cleanup true, deleted", tempDir


def _downloadWeather(start, end, airport, workDir):
    """
    Download weather CSV data to workDir. 1 file for each day between start and
    end (YYYY-MM-DD format). Location is set by airport (three letter airport code, e.g. DCA).
    """
    logger.info(
        'Downloading weather data... (start=%s, end=%s, airport=%s)', start, end, airport)
    # Parse start and end dates.
    start_dt = datetime.strptime(start, "%Y-%m-%d")
    end_dt = datetime.strptime(end, "%Y-%m-%d")
    # Calculate the number of days to fetch.
    num_days = (end_dt - start_dt).days
    work_day = start_dt
    # Generate URLs and get data.
    for i in range(num_days):
        year = work_day.year
        month = work_day.month
        day = work_day.day
        address = "http://www.wunderground.com/history/airport/{}/{:d}/{:d}/{:d}/DailyHistory.html?format=1".format(
            airport, year, month, day)
        filename = pJoin(
            workDir, "weather_{}_{:d}_{:d}_{:d}.csv".format(airport, year, month, day))
        if os.path.isfile(filename):
            continue  # We have the file already, don't re-download it.
        try:
            f = urllib.urlretrieve(address, filename)
        except:
            print("ERROR: unable to get data from URL " + address)
            continue  # Just try to grab the next one.
        work_day = work_day + timedelta(days=1)  # Advance one day


def _airportCodeToLatLon(airport):
    ''' Airport three letter code -> lat/lon of that location. '''
    try:
        logger.debug('Downloading geo coordinates for airport: %s', airport)
        url2 = urllib2.urlopen(
            'http://www.airport-data.com/airport/' + airport + '/#location')
        soup = BeautifulSoup(url2)
        latlon_str = str(soup.find(
            'td', class_='tc0', text='Longitude/Latitude:').next_sibling.contents[1])
        p = re.compile('([0-9\.\-\/])+')
        latlon_val = p.search(latlon_str)
        latlon_val = latlon_val.group()
        # latlon_split[0] is longitude; latlon_split[1] is latitude
        latlon_split = latlon_val.split('/')
        lat = float(latlon_split[1])
        lon = float(latlon_split[0])
    except urllib2.URLError, e:
        print 'Requested URL generated error code:', e.code
        lat = float(raw_input('Please enter latitude manually:'))
        lon = float(raw_input('Please enter longitude manually:'))
    return (lat, lon)


def _getPeakSolar(airport, workDir, dniScale=1.0, dhiScale=1.0, ghiScale=1.0):
    ''' get the peak non-cloudy solar data from a locale.  takes the ten most solar-energetic days and averages
            the values out into one 24-hour TMY3 file.'''
    lat, lon = _airportCodeToLatLon(airport)
    # Get metadata file.
    metaFileName = "TMY3_StationsMeta.csv"
    address = 'http://rredc.nrel.gov/solar/old_data/nsrdb/1991-2005/tmy3/TMY3_StationsMeta.csv'
    destination = pJoin(workDir, metaFileName)
    urllib.urlretrieve(address, destination)  # if this fails, we let it break.
    metaFile = open(destination)
    # Parse metadata file.
    metaFileReader = csv.reader(metaFile, delimiter=',')
    # NOTE: first line is headers.
    metaFileRows = [line for line in metaFileReader]
    metaHeaders = metaFileRows.pop(0)
    # find our desired column indices
    latItem = next(x for x in metaHeaders if 'Latitude' in x)
    longItem = next(x for x in metaHeaders if 'Longitude' in x)
    idItem = next(x for x in metaHeaders if 'USAF' in x)
    latIndex = metaHeaders.index(latItem)
    longIndex = metaHeaders.index(longItem)
    idIndex = metaHeaders.index(idItem)
    stationDist = []
    for row in metaFileRows:
        try:
            x = float(row[latIndex]) - lat
            y = float(row[longIndex]) - lon
            stationDist.append((x * x + y * y, row[idIndex]))
        except:
            pass  # 'bad' line
    # Find nearest station based on metadata CSV.
    minDist = min([line[0] for line in stationDist])
    stationResult = [line[1] for line in stationDist if line[0] == minDist]
    stationId = stationResult[0]  # ID string from the first result
    # Get specified TMY csv file.
    tmyURL = 'http://rredc.nrel.gov/solar/old_data/nsrdb/1991-2005/data/tmy3/' + \
        stationId + 'TYA.csv'
    tmyResult = urllib.urlretrieve(
        tmyURL, pJoin(workDir, stationId + 'TYA.csv'))
    tmyFile = open(tmyResult[0])
    tmyReader = csv.reader(tmyFile, delimiter=',')
    tmyLines = [line for line in tmyReader]
    tmyHeader = tmyLines.pop(0)
    tmyColumns = tmyLines.pop(0)
    seasonDict = {1: "Winter", 2: "Winter", 3: "Spring", 4: "Spring", 5: "Spring", 6:
                  "Summer", 7: "Summer", 8: "Summer", 9: "Fall", 10: "Fall", 11: "Fall", 12: "Winter"}
    seasonList = ["Winter", "Spring", "Summer", "Fall"]
    dateItem = next(x for x in tmyColumns if 'Date' in x)
    ghiItem = next(x for x in tmyColumns if 'GHI (W/m^2)' in x)
    dniItem = next(x for x in tmyColumns if 'DNI (W/m^2)' in x)
    dhiItem = next(x for x in tmyColumns if 'DHI (W/m^2)' in x)
    dateIndex = tmyColumns.index(dateItem)
    ghiIndex = tmyColumns.index(ghiItem)
    dniIndex = tmyColumns.index(dniItem)
    dhiIndex = tmyColumns.index(dhiItem)
    dateFormat = "%m/%d/%Y"
    dayDict = {}
    for line in tmyLines:
        lineDate = datetime.strptime(line[dateIndex], dateFormat)
        if lineDate in dayDict:
            dayDict[lineDate].append(line)
        else:
            dayDict[lineDate] = [line]
    # Each entry in dayDict is now a 24-item list.
    energyDict = {}
    for season in seasonList:
        energyDict[season] = []
    for key in dayDict:  # for each day,
        day = dayDict[key]
        # calculate using irradiances in tmy3 file for a day
        dhi = [float(value[dhiIndex]) for value in day]
        dni = [float(value[dniIndex]) for value in day]
        ghi = [float(value[ghiIndex]) for value in day]
        values = (math.fsum(dni), math.fsum(dhi), math.fsum(ghi))
        energy = values[0] * dniScale + values[1] * \
            dhiScale + values[2] * ghiScale
        season = seasonDict[key.month]
        energyDict[season].append((key, (dni, dhi, ghi), energy))
    # for each of four seasons,
    solarHeader = "Time(HH:MM),GHI_Normal,DNI_Normal,DHI_Normal\n"
    for season in seasonList:
        # sort by energy
        data = sorted(energyDict[season], key=lambda dayItem: dayItem[2])
        #  * pick out top 10 days
        topDays = data[-10:]
        #  * write file with average of those ten days
        tDni = [0.0] * 25
        tDhi = [0.0] * 25
        tGhi = [0.0] * 25
        for day in topDays:
            dni, dhi, ghi = day[1]
            for i in range(len(dni)):
                tDni[i] += dni[i]
                tDhi[i] += dhi[i]
                tGhi[i] += ghi[i]
        # write average day to file
        fileName = "solar_{}_{}.csv".format(airport, season.lower())
        outFile = open(pJoin(workDir, fileName), "w")
        # Time(HH:MM), GHI_Normal, DNI_Normal and DHI_Normal
        outFile.write(solarHeader)
        smPsf = 10.7639104  # square feet ~ source Google
        for i in range(24):
            outFile.write("{}:00,{},{},{}\n".format(str(i), str(
                tGhi[i] / 10 / smPsf), str(tDni[i] / 10 / smPsf), str(tDhi[i] / 10 / smPsf)))
        outFile.close()


class Weather:

    ''' Used to store data in _processWeather. '''
    Time = ""
    Temp = 68.0
    Humi = 10.0
    Wind = 2.5
    Cond = "Sunny"
    Data = 0
    Seas = ""
    Solar = 0
    TzDelta = 0

    def __init__(self):
        pass

    def Build(self, tm, dt, tz, t, h, w, c, d):
        seasonDict = {1: "Winter", 2: "Winter", 3: "Spring", 4: "Spring", 5: "Spring", 6:
                      "Summer", 7: "Summer", 8: "Summer", 9: "Fall", 10: "Fall", 11: "Fall", 12: "Winter"}
        self.Temp = float(t)
        self.Humi = float(h)
        self.Wind = w
        self.Cond = c  # 3-tuple
        self.Data = d  # csv-split line as a list
        self.TzDelta = tz
        dt2 = dt.split("<")
        t1 = datetime.strptime(dt2[0], "%Y-%m-%d %H:%M:%S")
        t2 = datetime.strptime(tm, "%I:%M %p")
        #self.Time = datetime(t1.year, t1.month, t1.day, t2.hour, t2.minute, 0)
        self.Time = t1 - tz
        self.Seas = seasonDict[self.Time.month]
        self.Solar = 0
        return self


def _processWeather(start, end, airport, workDir, interpolate="linear"):
    lat, lon = _airportCodeToLatLon(airport)

    def latlonprocess(lat, lon):
        minlat, lat = modf(lat)
        minlat = abs(int(minlat * 60))
        lat_string = '$lat_deg=' + \
            str(int(lat)) + '\n' + '$lat_min=' + str(minlat) + '\n'
        minlon, lon = modf(lon)
        minlon = abs(int(minlon * 60))
        lon_string = '$long_deg=' + \
            str(int(lon)) + '\n' + '$long_min=' + str(minlon) + '\n'
        return lat_string, lon_string

    lat_string, lon_string = latlonprocess(lat, lon)
    ''' Take CSV files in workDir from _downloadWeather and _getPeakSolar, and combine them into a CSV that can be read into GLD's climate object. '''
    startDate = datetime.strptime(start, "%Y-%m-%d")
    endDate = datetime.strptime(end, "%Y-%m-%d")
    # [0],    [1],         [2],       [3],     [4],                 [5],          [6],           [7],          [8],          [9],            [10],  [11],      [12],          [13]
    # TimePST,TemperatureF,Dew PointF,Humidity,Sea Level PressureIn,VisibilityMPH,Wind Direction,Wind SpeedMPH,Gust SpeedMPH,PrecipitationIn,Events,Conditions,WindDirDegrees,DateUTC<br />
    # 12:53 AM,44.1,43.0,96,29.99,9.0,Calm,Calm,-,N/A,,Overcast,0,2010-03-01 08:53:00<br />
    # condition dictionary
    moreConditionDict = {	"Light Drizzle": (0.3, 1.05, 0.39),  # sri start
                          "Drizzle": (0.2, 1.065, 0.32),
                          "Heavy Drizzle": (0.1, 1.1, 0.28),
                          "Light Rain": (0.2, 1.15, 0.34),
                          "Rain": (0.61, 1.765, 0.83),
                          "Heavy Rain": (0, 1.015, 0.2),
                          "Light Snow": (0, 1.805, 0.32),
                          "Snow": (0, 0.97, 0.2),
                          "Heavy Snow": (0, 1.585, 0.25),
                          "Light Snow Grains": (0.05, 1.925, 0.68),
                          "Snow Grains": (0, 1.37, 0.34),
                          "Heavy Snow Grains": (0, 1.42, 0.25),
                          # from 'light snow'
                          "Light Ice Crystals": (0, 1.805, 0.32),
                          # snow
                          "Ice Crystals": (0, 0.97, 0.2),
                          # heavy snow
                          "Heavy Ice Crystals": (0, 1.585, 0.25),
                          "Light Ice Pellets": (0.1, 1.39, 0.32),
                          "Ice Pellets": (0, 1.405, 0.3),
                          "Heavy Ice Pellets": (0, 1.48, 0.29),
                          # from 'light rain'
                          "Light Hail": (0.2, 1.15, 0.34),
                          # rain
                          "Hail": (0.61, 1.765, 0.83),
                          # heavy rain
                          "Heavy Hail": (0, 1.015, 0.2),
                          # light fog
                          "LightMist": (0, 1.45, 0.23),
                          # fog
                          "Mist": (0, 1.435, 0.22),
                          # heavy fog
                          "Heavy Mist": (0, 1.24, 0.24),
                          "Light Fog": (0, 1.45, 0.23),
                          "Fog": (0, 1.435, 0.22),
                          "Heavy Fog": (0, 1.24, 0.24),
                          "Light Fog Patches": (0, 1.45, 0.23),
                          "Fog Patches": (0, 1.435, 0.22),
                          "Heavy Fog Patches": (0, 1.24, 0.24),
                          "Partly Cloudy": (0.86, 1.225, 0.95),
                          # light fog
                          "Light Smoke": (0, 1.45, 0.23),
                          # fog
                          "Smoke": (0, 1.435, 0.22),
                          # heavy fog
                          "Heavy Smoke": (0, 1.24, 0.24),
                          # light haze
                          "Light Volcanic Ash": (0.14, 1, 0.5),
                          # haze
                          "Volcanic Ash": (0.11, 1.01, 0.46),
                          # heavy haze
                          "Heavy Volcanic Ash": (0.07, 1.06, 0.35),
                          # light haze
                          "Light Widespread Dust": (0.14, 1, 0.5),
                          # haze
                          "Widespread Dust": (0.11, 1.01, 0.46),
                          # heavy haze
                          "Heavy Widespread Dust": (0.07, 1.06, 0.35),
                          # light haze
                          "Light Sand": (0.14, 1, 0.5),
                          # haze
                          "Sand": (0.11, 1.01, 0.46),
                          # heavy haze
                          "Heavy Sand": (0.07, 1.06, 0.35),
                          "Light Haze": (0.14, 1, 0.5),
                          "Haze": (0.11, 1.01, 0.46),
                          "Heavy Haze": (0.07, 1.06, 0.35),
                          # light rain
                          "Light Spray": (0.2, 1.15, 0.34),
                          # rain
                          "Spray": (0.61, 1.765, 0.83),
                          # heavy rain
                          "Heavy Spray": (0, 1.015, 0.2),
                          # light haze
                          "Light Dust Whirls": (0.14, 1, 0.5),
                          # haze
                          "Dust Whirls": (0.11, 1.01, 0.46),
                          # heavy haze
                          "Heavy Dust Whirls": (0.07, 1.06, 0.35),
                          # light haze
                          "Light Sandstorm": (0.14, 1, 0.5),
                          # haze
                          "Sandstorm": (0.11, 1.01, 0.46),
                          # heavy haze
                          "Heavy Sandstorm": (0.07, 1.06, 0.35),
                          # light blowing snow sri
                          # start
                          "Light Low Drifting Snow": (0.07, 2.7, 0.7),
                          # blowing snow
                          "Low Drifting Snow": (0.02, 3.32, 0.72),
                          # heavy blowing snow
                          "Heavy Low Drifting Snow": (0, 3, 0.5),
                          # light haze
                          "Light Low Drifting Widespread Dust": (0.14, 1, 0.5),
                          # haze
                          "Low Drifting Widespread Dust": (0.11, 1.01, 0.46),
                          # heavy haze
                          "Heavy Low Drifting Widespread Dust": (0.07, 1.06, 0.35),
                          # light haze
                          "Light Low Drifting Sand": (0.14, 1, 0.5),
                          # haze
                          "Low Drifting Sand": (0.11, 1.01, 0.46),
                          # heavy haze
                          "Heavy Low Drifting Sand": (0.07, 1.06, 0.35),
                          "Light Blowing Snow": (0.07, 2.9, 0.7),
                          "Blowing Snow": (0.02, 3.32, 0.72),
                          "Heavy Blowing Snow": (0, 3, 0.5),
                          # light haze
                          "Light Blowing Widespread Dust": (0.14, 1, 0.5),
                          # haze
                          "Blowing Widespread Dust": (0.11, 1.01, 0.46),
                          # heavy haze
                          "Heavy Blowing Widespread Dust": (0.07, 1.06, 0.35),
                          # light haze
                          "Light Blowing Sand": (0.14, 1, 0.5),
                          # haze
                          "Blowing Sand": (0.11, 1.01, 0.46),
                          # heavy haze
                          "Heavy Blowing Sand": (0.07, 1.06, 0.35),
                          # light fog
                          "Light Rain Mist": (0, 1.45, 0.23),
                          # fog
                          "Rain Mist": (0, 1.435, 0.22),
                          # heavy fog
                          "Heavy Rain Mist": (0, 1.24, 0.24),
                          # light rain
                          "Light Rain Showers": (0.2, 1.15, 0.34),
                          # rain
                          "Rain Showers": (0.61, 1.765, 0.83),
                          # heavy rain
                          "Heavy Rain Showers": (0, 1.015, 0.2),
                          # light snow
                          "Light Snow Showers": (0, 1.805, 0.32),
                          # snow
                          "Snow Showers": (0, 0.97, 0.2),
                          # heavy snow
                          "Heavy Snow Showers": (0, 1.585, 0.25),
                          # light blowing snow
                          "Light Snow Blowing Snow Mist": (0.07, 2.9, 0.7),
                          # blowing snow
                          "Snow Blowing Snow Mist": (0.02, 3.32, 0.72),
                          # heavy blowing snow
                          "Heavy Snow Blowing Snow Mist": (0, 3, 0.5),
                          # light ice pellets
                          "Light Ice Pellet Showers": (0.1, 1.39, 0.32),
                          # ice pellets
                          "Ice Pellet Showers": (0, 1.405, 0.3),
                          # heavy ice pellets
                          "Heavy Ice Pellet Showers": (0, 1.48, 0.29),
                          # light ice pellets
                          "Light Hail Showers": (0.1, 1.39, 0.32),
                          # ice pellets
                          "Hail Showers": (0, 1.405, 0.3),
                          # heavy ice pellets
                          "Heavy Hail Showers": (0, 1.48, 0.29),
                          # light ice pellets
                          "Light Small Hail Showers": (0.1, 1.37, 0.32),
                          # ice pellets
                          "Small Hail Showers": (0, 1.405, 0.3),
                          # heavy ice pellets
                          "Heavy Small Hail Showers": (0, 1.48, 0.29),
                          # heavy ice pellets
                          "Heavy Small Hail": (0, 1.48, 0.29),
                          "Light Thunderstorm": (0.36, 1.635, 0.74),
                          "Thunderstorm": (0.25, 2.21, 0.84),
                          "Heavy Thunderstorm": (0.1, 1.375, 0.45),
                          # Light Thunderstorm (LT)
                          "Light Thunderstorms and Rain": (0.36, 1.635, 0.74),
                          # Thunderstorm (T)
                          "Thunderstorms and Rain": (0.25, 2.21, 0.84),
                          # Heavy Thunderstorm (HT)
                          "Heavy Thunderstorms and Rain": (0.1, 1.375, 0.45),
                          # LT
                          "Light Thunderstorms and Snow": (0.7, 1.15, 0.8),
                          # T
                          "Thunderstorms and Snow": (0.25, 2.21, 0.84),
                          # HT
                          "Heavy Thunderstorms and Snow": (0.1, 1.375, 0.45),
                          # LT
                          "Light Thunderstorms and Ice Pellets": (0.36, 1.635, 0.74),
                          # T
                          "Thunderstorms and Ice Pellets": (0.25, 2.21, 0.84),
                          # HT
                          "Heavy Thunderstorms and Ice Pellets": (0.1, 1.375, 0.45),
                          # LT
                          "Light Thunderstorms with Hail": (0.36, 1.635, 0.74),
                          # T
                          "Thunderstorms with Hail": (0.25, 2.21, 0.84),
                          # HT
                          "Heavy Thunderstorms with Hail": (0.1, 1.375, 0.45),
                          # LT
                          "Light Thunderstorms with Small Hail": (0.36, 1.635, 0.74),
                          # T
                          "Thunderstorms with Small Hail": (0.25, 2.21, 0.84),
                          # HT
                          "Heavy Thunderstorms with Small Hail": (0.1, 1.375, 0.45),
                          # light rain
                          "Light Freezing Drizzle": (0.2, 1.15, 0.34),
                          # rain
                          "Freezing Drizzle": (0.61, 1.765, 0.83),
                          # heavy rain
                          "Heavy Freezing Drizzle": (0, 1.015, 0.2),
                          # light ice pellets
                          "Light Freezing Rain": (0.1, 1.39, 0.32),
                          # ice pellets
                          "Freezing Rain": (0, 1.405, 0.3),
                          # heavy ice pellets
                          "Heavy Freezing Rain": (0, 1.48, 0.29),
                          # light fog
                          "Light Freezing Fog": (0, 1.45, 0.23),
                          # fog
                          "Freezing Fog": (0, 1.435, 0.22),
                          # heavy fog
                          "Heavy Freezing Fog": (0, 1.24, 0.24),
                          # light fog
                          "Patches of Fog": (0, 1.45, 0.23),
                          # fog
                          "Shallow Fog": (0, 1.435, 0.22),
                          # heavy fog
                          "Partial Fog": (0, 1.24, 0.24),
                          "Overcast": (0.07, 2.3, 0.6),
                          "Clear": (1.0, 1.0, 1.0),
                          "Mostly Cloudy": (0.6, 1.395, 0.88),
                          "Scattered Clouds": (0.42, 1.915, 0.75),
                          # light ice pellets
                          "Small Hail": (0.1, 1.39, 0.32),
                          # heavy haze
                          "Squalls": (0.07, 1.06, 0.35),
                          # mostly cloudy
                          "Funnel Cloud": (0.6, 1.395, 0.88),
                          # unknown
                          "Unknown Precipitation": (0.17, 0.35, 0.55),
                          "Unknown": (0.17, 0.35, 0.55),
                          "": (1.0, 1.0, 1.0)}  # no data in WU-default set. sri done
    seasonDict = {1: "Winter", 2: "Winter", 3: "Spring", 4: "Spring", 5: "Spring", 6:
                  "Summer", 7: "Summer", 8: "Summer", 9: "Fall", 10: "Fall", 11: "Fall", 12: "Winter"}
    # interpolation options
    interpolateList = ["none", "linear", "quadratic"]
    # scan for files
    fileList = os.listdir(workDir)
    filePtrn = re.compile(
        "weather_(?P<loc>[A-Za-z0-9]+)_(?P<raw_date>[0-9]+_[0-9]+_[0-9]+).csv")
    matchedFiles = list(filter(filePtrn.match, fileList))
    # identify desired files
    matchedList = [filePtrn.match(x) for x in matchedFiles]
    fileParts = [m.groupdict() for m in matchedList]
    filteredParts = list(filter(lambda x: x["loc"] == airport, fileParts))
    # filteredParts now contains a list of dictionaries where "loc" == airport
    fileDict = {}
    for part in filteredParts:
        # for part in filterDict:
        part["date"] = datetime.strptime(part["raw_date"], "%Y_%m_%d")
        part["file"] = "weather_{}_{}.csv".format(
            part["loc"], part["raw_date"])
        fileDict[part["date"]] = part
    # get timedelta
    timeDiff = endDate - startDate
    timeRange = [startDate + timedelta(days=n)
                 for n in range(0, timeDiff.days)]
    useFiles = []
    for eachDay in timeRange:
        if eachDay in fileDict:
            useFiles.append(fileDict[eachDay])
    # useFiles now has a list of all the files in the range that we want to use
    myData = []
    weatherData = []
    for eachFile in useFiles:
        myFile = open(pJoin(workDir, eachFile["file"]), "r")
        myLines = myFile.readlines()
        if len(myLines) < 3:
            print 'WARNING:No Data available for this day-Skipping for date:', eachFile["raw_date"]
            continue
        invalid_phrase = 'No daily or hourly history data available'
        if invalid_phrase in str(myLines[2]):
            if startDate == eachFile["date"]:
                sys.exit(
                    "ERROR: Given startDate has no WU recorded data. Please give a startDate with some WU data. Use Example: http://www.wunderground.com/history/airport/AJO/2012/7/2/DailyHistory.html?format=126 .Edit airport code, date to check as per your request")
            print 'WARNING:BAD RECORD/DAY FILE-Skipping for date:', eachFile["raw_date"]
            continue
        #myLines = [line+","+eachFile["file"] for line in myLinesPre]
        myData.extend(myLines)
    # remove all "<br />" lines
    weatherDataInt = list(filter(lambda x: len(x) > 1, myData))
    # capture all header lines
    weatherHeader = list(filter(lambda x: "Time" in x, weatherDataInt))
    # remove all header lines
    weatherDataTrim = list(filter(lambda x: "Time" not in x, weatherDataInt))
    # split into a list of lists
    weatherSplit = [str.split(line, ",") for line in weatherDataTrim]
    weatherKeys = str.split(weatherHeader[0], ",")
    # weatherData = [dict(zip(weatherKeys, thisSplit)) for thisSplit in
    # weatherSplit] # makes a dictionary out of things, to make it
    # complicated...
    weatherData = weatherSplit
    # TimePST,     TemperatureF, Dew PointF, Humidity, Sea Level PressureIn, VisibilityMPH, Wind Direction, Wind SpeedMPH,
    # ['1:53 AM', '43.0',        '42.1',    '97',      '29.99',              '9.0',        'Calm',          'Calm',
    # (cont'd)
    # Gust SpeedMPH, PrecipitationIn, Events,  Conditions,    WindDirDegrees, DateUTC<br />
    # '-',           'N/A',           'Fog',   'Shallow Fog', '0',            '2010-03-01 09:53:00<br />\n']
    # record the time, temp, humidity, wind, conditions, and date.
    # get time & date indices
    timeIndex = 0
    utcIndex = 0
    for index, key in enumerate(weatherKeys):  # works to this point
        if "Time" in key:
            timeIndex = index
        if "Date" in key:
            utcIndex = index
    # slice timezone from keys
    tz = weatherKeys[timeIndex][4:7]
    if tz == ('PDT'):
        timezone_offset = '$timezone_offset=' + str(-8) + '\n'
    elif tz == ('PST'):
        timezone_offset = '$timezone_offset=' + str(-8) + '\n'
    elif tz == ('MDT'):
        timezone_offset = '$timezone_offset=' + str(-7) + '\n'
    elif tz == ('MST'):
        timezone_offset = '$timezone_offset=' + str(-7) + '\n'
    elif tz == ('CDT'):
        timezone_offset = '$timezone_offset=' + str(-6) + '\n'
    elif tz == ('CST'):
        timezone_offset = '$timezone_offset=' + str(-6) + '\n'
    elif tz == ('EDT'):
        timezone_offset = '$timezone_offset=' + str(-5) + '\n'
    elif tz == ('EST'):
        timezone_offset = '$timezone_offset=' + str(-5) + '\n'
    else:
        timezone_offset = '$timezone_offset=unkown\n'
    # use the first sample to determine TZ offset
    firstDt = datetime.strptime(weatherData[0][timeIndex], "%I:%M %p")
    t1 = datetime(year=startDate.year, month=startDate.month,
                  day=startDate.day, hour=firstDt.hour, minute=firstDt.minute)  # local
    t2 = datetime.strptime(
        weatherData[0][utcIndex].split("<")[0], "%Y-%m-%d %H:%M:%S")  # GMT
    tzDelta = t2 - t1
    # replace "Calm" wind with 0
    windIndex = 0
    windKey = "Wind SpeedMPH"
    if windKey in weatherKeys:
        windIndex = weatherKeys.index(windKey)
        windDataList = [sample[windIndex] for sample in weatherData]
        # print(windDataList)
        # if windspeed has a value, keep the value. if it has text:"calm", give
        # it a value
        for index, entry in enumerate(windDataList):
            if entry == "Calm":
                weatherData[index][windIndex] = 0.0
                #print("replacing 'Calm' at time "+str(weatherData[index][utcIndex]))
            else:
                #print("not replacing '"+str(entry)+"' at time "+str(weatherData[index][utcIndex]))
                weatherData[index][windIndex] = float(
                    weatherData[index][windIndex])
    else:
        windIndex = -1
        # error and explode
    # replace "N/A" humidity with 0
    humidKey = "Humidity"
    humidIndex = 0
    # if humidspeed has a value, keep the value. if it has text:"N/A", give it
    # a value
    if humidKey in weatherKeys:
        humidIndex = weatherKeys.index(humidKey)
        for index, entry in enumerate(sample[humidIndex] for sample in weatherData):
            if entry == "N/A":
                weatherData[index][humidIndex] = 0.0
    else:
        humidIndex = -1
        # error and explode
    # replace 'Conditions" with dictionary value
    condKey = "Conditions"
    condIndex = 0
    if condKey in weatherKeys:
        condIndex = weatherKeys.index(condKey)
        # replace the "text" weather conditions with "values" from huge
        # dictionary created above
        for index, entry in enumerate(sample[condIndex] for sample in weatherData):
            if entry in moreConditionDict.keys():
                weatherData[index][condIndex] = moreConditionDict[entry]
                #print("index {:d} to ".format(index)+str(weatherData[index][condIndex]))
                if entry is "":
                    print "WARNING: Weather Condition missing in WeatherUnderground datapage"
            else:
                print(
                    "index {:d} invalid conditions '{}'".format(index, entry))
    else:
        condIndex = -1
        # error and explode
    # get temperature index
    heatKey = "TemperatureF"
    heatIndex = 0
    if heatKey in weatherKeys:
        heatIndex = weatherKeys.index(heatKey)
    else:
        heatIndex = -1
    # convert to useful values
    weatherList = []
    # def Weather(self, tm, dt, tz, t, h, w, c, d):
    # Now in weatherData, we have all text (ex: calm, cloudy, N/A) replaced
    # with numbers
    for entry in weatherData:
        sample = Weather().Build(entry[timeIndex], entry[utcIndex], tzDelta, entry[
            heatIndex], entry[humidIndex], entry[windIndex], entry[condIndex], entry)
        # print tzDelta
        # print sample.Data # print all records going to be append to
        # weatherList
        weatherList.append(sample)
    # sanity-check numbers
    for index, entry in enumerate(weatherList):
        # print entry.Data # print all records going in weatherList
        # * temperature
        if entry.Temp > 150.0 or entry.Temp < -20:
            if index > 0:
                entry.Temp = weatherList[index - 1].Temp
            else:
                # if first value is bad, snag the first good value
                n = 1
                while (weatherList[n].Temp > 150.0 or weatherList[n].Temp < -20) and n < len(weatherList):
                    n += 1
                entry.Temp = weatherList[n].Temp
        # * humidity
        if entry.Humi > 100.0 or entry.Humi < 0.0:
            if index > 0:
                entry.Humi = weatherList[index - 1].Temp
            else:
                # if first value is bad, snag the first good value
                n = 1
                while (weatherList[n].Humi > 100.0 or weatherList[n].Humi < 0) and n < len(weatherList):
                    n += 1
                entry.Humi = weatherList[n].Humi
        # * wind speed
        if entry.Wind > 200.0 or entry.Wind < -1.0:
            if index > 0:
                entry.Wind = weatherList[index - 1].Wind
            else:
                # if first value is bad, snag the first good value
                n = 1
                while (n < len(weatherList)):
                    if weatherList[n].Wind > 200.0:
                        print(
                            "wind speed " + str(weatherList[n].Wind) + " at " + str(n) + " out of range (above)")
                        n += 1
                    if weatherList[n].Wind < -1.0:
                        print(
                            "wind speed " + str(weatherList[n].Wind) + " at " + str(n) + " out of range (below)")
                        n += 1
                    else:
                        break
                if n < len(weatherList):
                    entry.Wind = weatherList[n].Wind
                else:
                    print(
                        "error getting wind value for sample at " + str(entry.Time))
        # * conditions
        if entry.Cond == "Unknown":
            if index > 0:
                entry.Cond = weatherList[index - 1].Cond
            else:
                # if first value is bad, snag the first good value
                n = 1
                while n < len(weatherList) and (weatherList[n].Cond == "Unknown"):
                    n += 1
                entry.Cond = moreConditionDict[weatherList[n].Cond]
    # add 00:00:00 to each day
    # remember we formed season based .csv files. grab them
    seasons = {	"Winter": ([], "solar_{}_winter.csv".format(airport)),
                "Spring": ([], "solar_{}_spring.csv".format(airport)),
                "Summer": ([], "solar_{}_summer.csv".format(airport)),
                "Fall": ([], "solar_{}_fall.csv".format(airport))}
    # load and parse solar files for key in seasons.keys():
    seasonCount = {	"Winter": 0,	"Spring": 0, "Summer": 0, "Fall": 0}
    for line in weatherList:
        seasonCount[line.Seas] += 1
    # now pick the season_.csv file that is non-zero i.e., the season of the
    # file month running
    for season in seasonCount:
        if seasonCount[season] == 0:
            continue
        # Time(HH:MM), GHI_Normal, DNI_Normal and DHI_Normal
        #  * {2-4} used for 'real data'.
        seasonData, seasonFileName = seasons[season]
        seasonFile = open(pJoin(workDir, seasonFileName), "r")
        # get the ideal irradiances to from the season_.csv file
        seasonFileLines = seasonFile.readlines()
        seasonFileLines.pop(0)  # header
        seasonDataStr = [str.split(line, ",") for line in seasonFileLines]
        # print(seasonDataStr)
        seasonData.extend([(float(data[2]), float(data[3]), float(data[1]))
                           for data in seasonDataStr])  # skip time in index 0
    # find solar data per-season, interpolate from hourly to the sample time,
    # add into weather dictionary
    for sample in weatherList:
        wDir, dif, glo = sample.Cond
        sampleHour = sample.Time.hour
        seasonData, Season = seasons[sample.Seas]
        dirMod, difMod, gloMod = seasonData[sampleHour]
        # multiply values from season_.csv with matching ratios in Conditions
        # dictionary
        sample.Solar = (wDir * dirMod, dif * difMod, glo * gloMod)
        #print(str(sample.Time)+": "+str(sample.Cond)+" * "+str(seasonData[sampleHour])+" = "+str(sample.Solar))
    # interpolate downloaded data into
    outData = []
    interval = timedelta(minutes=5)
    lerp = lambda x, y, r: x + (y - x) * r

    def qerp(x, y0, y1, y2, x0, x1, x2):
        if x == x0:
            return y0
        if x == x1:
            return y1
        if x == x2:
            return y2
        if(x0 == x1):
            print("QERP ERROR: x0 == x1")
            return 0.0
        if(x1 == x2):
            print("QERP ERROR: x1 == x2")
            return 0.0
        if x0 == x2:
            print("QERP ERROR: x0 == x2")
            return 0.0
        return (x - x1) * (x - x2) / (x0 - x1) / (x0 - x2) * y0 + (x - x0) * (x - x2) / (x1 - x0) / (x1 - x2) * y1 + (x - x0) * (x - x1) / (x2 - x0) / (x2 - x1) * y2
    epoch = datetime(1970, 1, 1)
    for index, entry in enumerate(weatherList):
        # write sample
        outData.append(entry)
        # if next step is more than 5 minutes ahead,
        if index + 1 >= len(weatherList):
            # we've run out of samples
            break
        #  * count number of 5 minute steps
        steps = 0
        timeStep = weatherList[index + 1].Time - weatherList[index].Time
        if "linear" in interpolate:
            if timeStep > interval:
                steps = int(math.floor(timeStep.seconds / interval.seconds))
                nxEntry = weatherList[index + 1]
                #  * for each step, write an interpolated value.
                for n in range(1, steps):
                    ratio = n * float(interval.seconds) / \
                        float(timeStep.seconds)
                    sample = Weather()
                    sample.Temp = lerp(entry.Temp, nxEntry.Temp, ratio)
                    sample.Humi = lerp(entry.Humi, nxEntry.Humi, ratio)
                    sample.Wind = lerp(entry.Wind, nxEntry.Wind, ratio)
                    sDir, sDif, sGlo = entry.Solar
                    nDir, nDif, nGlo = nxEntry.Solar
                    # Below: all the normal existing irradiances are
                    # modified/interpolated
                    sample.Solar = (
                        lerp(sDir, nDir, ratio), lerp(sDif, nDif, ratio), lerp(sGlo, nGlo, ratio))
                    sample.Time = entry.Time + n * interval
                    # For the days not starting at midnight and doesn't go till 11:55PM
                    # The script interpolates for all the remaining hours based on the next
                    # available record. This is causing to generate incorrect data.
                    # Example: gnerating irradiance values at night
                    # (IMPOSSIBLE! right?)
                    if sample.Time < entry.Time + timedelta(hours=1):
                        # we want to stop "saving" interpolated records when we hit the very last record of the day.
                        # without the if case below, the script will create a
                        # "non-existing" extra hour for that day.
                        if weatherList[index + 1].Time.strftime('%Y-%m-%d') <= weatherList[index].Time.strftime('%Y-%m-%d'):
                            sample.Seas = seasonDict[sample.Time.month]
                            outData.append(sample)
        elif "quadratic" in interpolate:
            if timeStep > interval:
                steps = int(math.floor(timeStep.seconds / interval.seconds))
                p0 = 0
                p1 = 0
                p2 = 0
                if index + 2 > len(weatherList):
                    # last sample, don't interpolate forward
                    break
                elif index + 2 == len(weatherList):
                    # need to use i-1, i, i+1 for reference points
                    p0 = weatherList[index - 1]
                    p1 = entry
                    p2 = weatherList[index + 1]
                else:
                    # full interpolation
                    p0 = entry
                    p1 = weatherList[index + 1]
                    p2 = weatherList[index + 2]
                for n in range(1, steps):
                    #t = float(n) * float(interval.seconds) + float(timeStep.seconds)
                    t = (n * interval + timeStep).total_seconds()
                    t1 = (p0.Time - epoch).total_seconds()
                    t2 = (p1.Time - epoch).total_seconds()
                    t3 = (p2.Time - epoch).total_seconds()
                    sample = Weather()
                    sample.Temp = qerp(
                        t, p0.Temp, p1.Temp, p2.Temp, t1, t2, t3)
                    sample.Humi = qerp(
                        t, p0.Humi, p1.Humi, p2.Humi, t1, t2, t3)
                    sample.Wind = qerp(
                        t, p0.Wind, p1.Wind, p2.Wind, t1, t2, t3)
                    aDir, aDif, aGlo = p0.Solar
                    bDir, bDif, bGlo = p1.Solar
                    cDir, cDif, cGlo = p2.Solar
                    sample.Solar = (qerp(t, aDir, bDir, cDir, t1, t2, t3), qerp(
                        t, aDif, bDif, cDif, t1, t2, t3), qerp(t, aGlo, bGlo, cGlo, t1, t2, t3))
                    sample.Time = entry.Time + n * interval
                    sample.Seas = seasonDict[sample.Time.month]
                    if sample.Wind < 0:
                        # clip, since qerp can take values below zero
                        sample.Wind = 0
                    outData.append(sample)
    # open and write the output file
    with open(pJoin(workDir, "weather.csv"), "w") as outFile:
        # write header
        outFile.write('#weather file\n')
        outFile.write(lat_string)
        outFile.write(lon_string)
        outFile.write(timezone_offset)
        outFile.write(
            'temperature,wind_speed,humidity,solar_dir,solar_diff,solar_global\n')
        outFile.write('#month:day:hour:minute:second\n')
        # write samples per-line
        for line in outData:
            if line.Time.month in range(1, 13):
                # write each line
                outFile.write("{}:{}:{}:{}:{},{},{},{},{},{},{}\n".format(line.Time.month, line.Time.day,
                                                                          line.Time.hour, line.Time.minute, line.Time.second, line.Temp, line.Wind,
                                                                          line.Humi, line.Solar[0], line.Solar[1], line.Solar[2]))


def zipCodeToClimateName(zipCode):
    ''' Maps zipcode from excel data to city, state, lat/lon. '''
    logger.info('Getting climate data for zipcode: %s', zipCode)
    # From excel file at:
    # https://www.gaslampmedia.com/download-zip-code-latitude-longitude-city-state-county-csv/

    def compareLatLon(LatLon, LatLon2):
        differenceLat = float(LatLon[0]) - float(LatLon2[0])
        differenceLon = float(LatLon[1]) - float(LatLon2[1])
        distance = math.sqrt(
            math.pow(differenceLat, 2) + math.pow(differenceLon, 2))
        return distance

    def safeListdir(path):
        try:
            logger.debug('Listing contents of %s', path)
            return os.listdir(path)
        except:
            logger.exception('Failed to list directory contents')
            return []

    ###
    omfDir = os.path.dirname(os.path.abspath(__file__))
    path = pJoin(omfDir, "data", "Climate")
    zipCodeStr = str(zipCode)
    climateNames = [x[:-5] for x in safeListdir(path)]
    climateCity = []
    lowestDistance = 1000
    # Parse .csv file with city/state zip codes and lat/lon
    zipCsvPath = pJoin(omfDir, "static", "zip_codes_states.csv")
    logger.debug('Reading %s', zipCsvPath)
    with open(zipCsvPath, 'rt') as f:
        reader = csv.reader(f, delimiter=',')
        rowcnt = 0
        for row in reader:
            rowcnt = rowcnt + 1
            for field in row:
                if field == zipCodeStr:
                    zipState = row[4]
                    zipCity = row[3]
                    ziplatlon = row[1], row[2]
                    logger.debug('Found zipcode information: state=%s, city=%s, latitide=%s, longitude=%s',
                                 zipState, zipCity, ziplatlon[0], ziplatlon[1])
        logger.info('Processed %d CSV rows', rowcnt)
    # Looks for climate data by looking at all cities in that state.
    # TODO: check other states too.
    # Filter only the cities in that state:
    try:
        for x in range(0, len(climateNames)):
            if (zipState + "-" in climateNames[x]):
                climateCity.append(climateNames[x])
    except:
        raise ValueError('Invalid Zipcode entered:', zipCodeStr)
    climateCity = [w.replace(zipState + "-", '') for w in climateCity]
    # Parse the cities distances to zipcode city to determine closest climate:
    logger.debug('Climate cities: %s', climateCity)
    for x in range(0, len(climateCity)):
        with open(zipCsvPath, 'rt') as f:
            reader = csv.reader(f, delimiter=',')
            for row in reader:
                city = row[3].replace(" ", "_")
                if ((row[4].lower() == zipState.lower()) and (city.lower() == str(climateCity[x]).lower())):
                    climatelatlon = row[1], row[2]
                    try:
                        distance = compareLatLon(ziplatlon, climatelatlon)
                        if (distance < lowestDistance):
                            latforpvwatts = int(
                                round((float(climatelatlon[0]) - 10) / 5.0) * 5.0)
                            lowestDistance = distance
                            found = x
                    except:
                        pass
    climateName = zipState + "-" + climateCity[found]
    logger.info('Climate Name: %s', climateName)
    return climateName, latforpvwatts


def _tests():
    print "Beginning to test weather.py"
    workDir = tempfile.mkdtemp()
    print "IAD lat/lon =", _airportCodeToLatLon("IAD")
    assert (
        38.947444, -77.459944) == _airportCodeToLatLon("IAD"), "airportCode lookup failed."
    print "Weather downloading to", workDir
    assert None == _downloadWeather("2010-03-01", "2010-04-01", "PDX", workDir)
    print "Peak solar extraction in", workDir
    assert None == _getPeakSolar(
        "PDX", workDir, dniScale=1.0, dhiScale=1.0, ghiScale=1.0)
    print "Pull weather and solar data together in", workDir
    assert None == _processWeather("2010-03-01", "2010-04-01", "PDX", workDir)
    print "Testing the full process together."
    assert None == makeClimateCsv(
        "2010-07-01", "2010-08-01", "IAD", pJoin(tempfile.mkdtemp(), "weatherDCA.csv"), cleanup=True)
    print "Testing the zip code to climate name conversion"
    assert ('MO-KANSAS_CITY', 30) == zipCodeToClimateName(64735)


if __name__ == "__main__":
    _tests()
