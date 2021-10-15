from math import cos, asin, sqrt, pi
import requests
import json
from urllib.parse import urlencode, quote


def convert_if_bool(value):
    if type(value) == bool:
        if value:
            return 1
        else:
            return 0
    else:
        return value


def georeverse(lat, lon):
    get_address_url = 'https://nominatim.openstreetmap.org/reverse?format=jsonv2&zoom=16&lat=' + str(lat) + '&lon=' + str(lon)
    response = requests.get(get_address_url)
    if response.status_code == 200:
        response = json.loads(response.text)
        return response['display_name']
    else:
        return False


def geolookup(locationtolookup):
    get_address_url = 'https://nominatim.openstreetmap.org/search?q='+quote(locationtolookup) + '&format=geocodejson&addressdetails=1&limit=1'
    response = requests.get(get_address_url)
    if response.status_code == 200:
        response = json.loads(response.text)
        try:
            response = response['features'][0]
            poi_info = {
                "poiInfoList": [{
                    "phone": "",
                    "waypointID": 0,
                    "lang": 1,
                    "src": "HERE",
                    "coord": {
                        "lat": response['geometry']['coordinates'][0],
                        "alt": 0,
                        "lon": response['geometry']['coordinates'][1],
                        "type": 0
                    },
                    "addr": response['properties']['geocoding']['label'],
                    "zip": "",
                    "placeid": response['properties']['geocoding']['label'],
                    "name": lookup
                }],
            }
            return poi_info
        except: return False
    else: return False


def get_location_temperature(weather_api_key, weather_provider, lat, lon):
    if weather_provider == 'DarkSky':
        get_weather_url = 'https://api.darksky.net/forecast/' + weather_api_key + '/' + str(lat) + ',' + str(lon) + '?units=si'
        response = requests.get(get_weather_url)
        if response.status_code == 200:
            response = json.loads(response.text)
            return response['currently']['temperature']
        else: return False
    elif weather_provider == 'OpenWeather':
        get_weather_url = 'https://api.openweathermap.org/data/2.5/weather?lat=' + str(lat) + '&lon=' + str(lon) + '&appid=' + weather_api_key + '&type=accurate&units=metric'
        response = requests.get(get_weather_url)
        if response.status_code == 200:
            response = json.loads(response.text)
            return response['main']['temp']
        else: return False
    else: return False

def distance(lat1, lon1, lat2, lon2):
    p = pi / 180
    a = 0.5 - cos((lat2 - lat1) * p) / 2 + cos(lat1 * p) * cos(lat2 * p) * (1 - cos((lon2 - lon1) * p)) / 2
    return 12742 * asin(sqrt(a))

def temp2hex(temp):
    if temp <= 14: return "00H"
    if temp >= 30: return "20H"
    return str.upper(hex(round(float(temp) * 2) - 28).split("x")[1]) + "H"  # rounds to .5 and transforms to Kia-hex (cut off 0x and add H at the end)

def hex2temp(hextemp):
    temp = int(hextemp[:2], 16) / 2 + 14
    if temp <= 14: return 14
    if temp >= 30: return 30
    return temp


#TODO google time from home
    #with google key calculate driving time from home