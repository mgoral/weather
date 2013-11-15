#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""
Copyright (C) 2013 Michal Goral.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import re
import argparse
import urllib.request
import urllib.error
import xml.etree.ElementTree as et
from string import Template
from datetime import datetime

class WeatherData:
    city = None
    country = None
    time = None
    temperature = None
    windspeed = None
    desc = None
    tempUnit = None
    speedUnit = None

    def __init__(self):
        self.setDateFormat("%Y-%m-%d %H:%M")
        self.setFormat("%c (%C),%d,%e,%T,%W")

    def setDateFormat(self, dateFormat):
        self._dateFormat = dateFormat

    def setFormat(self, stringFormat):
        """
        Format specification:
        %c - city
        %C - country
        %d - date with time
        %t - temperature (without units)
        %T - temperature (with units)
        %w - windspeed (without units)
        %W - windspeed (with units)
        %e - description
        """
        stringFormat = stringFormat.replace('$', '$$')
        stringFormat = stringFormat.replace("%", "$")
        self._format = Template(stringFormat)

    def __str__(self):
        printMapping = {
            'c': self.city,
            'C': self.country,
            'd': self.time.strftime(self._dateFormat),
            't': self.temperature,
            'T': "%s°%s" % (self.temperature, self.tempUnit),
            'w': self.windspeed,
            'W': "%s %s" % (self.windspeed, self.speedUnit),
            'e': self.desc,
        }
        return self._format.substitute(printMapping)

def initArgumentParser():
    parser = argparse.ArgumentParser(
        description = "Fetch and print current weather in specified format.")

    parser.add_argument('locations',
        metavar='WOEID', type=int, nargs = '+', help = 'WOEID locations')

    parser.add_argument('-f', '--file',
        help = 'Append results to a file instead of stdout.')
    parser.add_argument('-F', '--format',
        default = None, help = 'Output weather in specified format (see: README).')
    parser.add_argument('-D', '--dateformat',
        default = None, help = 'Format of output date/time (see: \'man strftime\')')
    parser.add_argument('--imperial',
        dest='units', action = 'store_const', const='f', default = 'c',
        help = 'Get weather in imperial units.')
    parser.add_argument('--now',
        action = 'store_true', help = 'Print current time instead of the fetched one.')

    return parser

def downloadWeather(location, units):
    address = "http://weather.yahooapis.com/forecastrss?w=%s&u=%s" % (location, units)
    try:
        resp = urllib.request.urlopen(address)
    except urllib.error.URLError as e:
        print("%s : %s" % (address, e))
        return None
    weather = resp.readall().decode('utf-8')
    return weather

def appendDataToFile(data, filename):
    with open(filename, 'a') as file_:
        file_.write("%s\n" % str(data))

def parseWeather(data):
    xmlnsFound = re.findall(r'xmlns:(\w+)="([^"]+?)"', data)
    ns = {}

    for xmlns in xmlnsFound:
        ns[xmlns[0].strip()] = xmlns[1].strip()

    root = et.fromstring(data)
    channel = root.find("channel")
    item = channel.find("item")

    units = channel.find("yweather:units", namespaces = ns)
    location = channel.find("yweather:location", namespaces = ns)
    wind = channel.find("yweather:wind", namespaces = ns)

    condition = item.find("yweather:condition", namespaces = ns)
    date = item.find("pubDate")

    weatherData = WeatherData()
    weatherData.city = location.attrib["city"]
    weatherData.country = location.attrib["country"]
    # Fri, 15 Nov 2013 12:59 pm CET
    weatherData.time = datetime.strptime(date.text, "%a, %d %b %Y %I:%M %p %Z")
    weatherData.temperature = condition.attrib["temp"]
    weatherData.desc = condition.attrib["text"]
    weatherData.windspeed = wind.attrib["speed"]

    weatherData.tempUnit = units.attrib["temperature"]
    weatherData.speedUnit = units.attrib["speed"]

    return weatherData

def main():
    parser = initArgumentParser()
    args = parser.parse_args()

    for location in args.locations:
        weatherXml = downloadWeather(location, args.units)
        if weatherXml is not None:
            weatherData = parseWeather(weatherXml)
            if (args.format is not None):
                weatherData.setFormat(args.format)
            if (args.dateformat is not None):
                weatherData.setDateFormat(args.dateformat)
            if (args.now is True):
                weatherData.time = datetime.now()

            if args.file:
                appendDataToFile(weatherData, args.file)
            else:
                print(weatherData)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        raise SystemExit(0)

