import time
import requests
import json
from urllib.parse import urlencode, quote
from weatherInfo import weatherInfo
from generic_lib import convert_if_bool

class ABRP():
	# ABRP API information: https://documenter.getpostman.com/view/7396339/SWTK5a8w?version=latest
    def __init__(self, abrp_carmodel, abrp_token, weather_api_key, weather_provider):
        self.abrp_carmodel = abrp_carmodel
        self.abrp_token = abrp_token
		# ABRP Telemetry API KEY - DO NOT CHANGE
        self.abrp_apikey = '6f6a554f-d8c8-4c72-8914-d5895f58b1eb'
        if len(weather_api_key) > 0:
            self.weatherInfo = weatherInfo(weather_api_key, weather_provider)
        else:
            self.weatherInfo = None
        return
        
    def send_abr_ptelemetry(self, soc, speed, charging, latitude, longitude ):
        if self.abrp_token != "":
            data = {'utc': time.time(), 'soc': soc, 'speed': speed, 'is_charging': convert_if_bool(charging),
					'car_model': self.abrp_carmodel}
            if latitude is not None:    data['lat'] = latitude
            if longitude is not None:   data['lon'] = longitude
            #if self.weather_provider is not None and self.weather_api_key is not None and latitude is not None and longitude is not None:
            if self.weatherInfo is not None:
                ext_temp = self.weatherInfo.get_location_temperature(latitude, longitude)
                if ext_temp is not False: data['ext_temp'] = ext_temp
            params = {'token': self.abrp_token, 'api_key': self.abrp_apikey, 'tlm': json.dumps(data, separators=(',', ':'))}
            response = requests.get('https://api.iternio.com/1/tlm/send?' + urlencode(params))
            if response.status_code == 200: return json.loads(response.text)
            else: return False
        else: return False
