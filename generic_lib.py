import time
from math import cos, asin, sqrt, pi
import sys
import urllib
import requests
import uuid
import json
import urllib.parse as urlparse
from urllib.parse import parse_qs, urlencode, quote_plus

def ConvertIfBool(value):
    if type(value) == bool:
        if value:
            return 1
        else:
            return 0
    else:
        return value

def GetLocationTemperature(DarkSkyApiKey, lat, lon):
    # TODO general: error handling with try and except / raise
    # TODO change Darksky
    getDarkSkyURL = 'https://api.darksky.net/forecast/' + DarkSkyApiKey + '/' + str(lat) + ',' + str(lon) + '?units=si'
    response = requests.get(getDarkSkyURL)
    if response.status_code == 200:
        response = json.loads(response.text)
        return response['currently']['temperature']
    else:
        print('NOK Weather')
        return -1

def SendABRPtelemetry(soc, speed, latitude, longitude, charging, abrp_carmodel, abrp_token,DarkSkyApiKey):
    # ABRP API information: https://documenter.getpostman.com/view/7396339/SWTK5a8w?version=latest
    # ABRP Telemetry API KEY - DO NOT CHANGE
    abrp_apikey = '6f6a554f-d8c8-4c72-8914-d5895f58b1eb'
    data = {}
    data['utc'] = time.time()
    data['soc'] = soc
    data['speed'] = speed
    data['lat'] = latitude
    data['lon'] = longitude
    data['is_charging'] = ConvertIfBool(charging)
    data['car_model'] = abrp_carmodel
    data['ext_temp'] = GetLocationTemperature(DarkSkyApiKey, latitude, longitude)
    params = {'token': abrp_token, 'api_key': abrp_apikey, 'tlm': json.dumps(data, separators=(',', ':'))}
    response = requests.get('https://api.iternio.com/1/tlm/send?' + urlencode(params))
    if response.status_code == 200:
        response = json.loads(response.text)
        return response
    else:
        print('NOK ABRP')
        return -1

def distance(lat1, lon1, lat2, lon2):
    p = pi / 180
    a = 0.5 - cos((lat2 - lat1) * p) / 2 + cos(lat1 * p) * cos(lat2 * p) * (1 - cos((lon2 - lon1) * p)) / 2
    return 12742 * asin(sqrt(a))