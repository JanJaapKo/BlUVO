import requests
import json

class weatherInfo():
    def __init__(self, weather_api_key, weather_provider):
        self.weather_api_key = weather_api_key
        self.weather_provider = weather_provider
        return
        
    def get_location_temperature(self, cur_lat, cur_lon):
        if self.weather_provider == 'DarkSky':
            get_weather_url = 'https://api.darksky.net/forecast/' + self.weather_api_key + '/' + str(cur_lat) + ',' + str(cur_lon) + '?units=si'
            response = requests.get(get_weather_url)
            if response.status_code == 200:
                response = json.loads(response.text)
                return response['currently']['temperature']
            else: return False
        elif self.weather_provider == 'OpenWeather':
            get_weather_url = 'https://api.openweathermap.org/data/2.5/weather?lat=' + cur_lat + '&lon=' + cur_lon + '&appid=' + self.weather_api_key + '&type=accurate&units=metric'
            response = requests.get(get_weather_url)
            if response.status_code == 200:
                response = json.loads(response.text)
                return response['main']['temp']
            else: return False
        else: return False
