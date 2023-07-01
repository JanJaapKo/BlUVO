#TODO add versioning
import requests
import uuid
import json
import logging
import random
import urllib.parse as urlparse
from exceptions import * 
from urllib.parse import parse_qs
from datetime import datetime, timedelta
from time import time
from generic_lib import temp2hex

class brandAuth():
    accessToken = None
    accessTokenExpiresAt = None
    controlToken = None
    controlTokenExpiresAt = None
    def __init__(self, car_brand):
        self.car_brand = car_brand
        self.ServiceId = "" #clientId in bluelinky
        self.BasicToken = ""
        self.CcspApplicationId = ""
        self.__stamp__ = ""
        self.BaseHost = "prd.eu-ccapi." + self.car_brand + ".com:8080"
        self.BaseURL = "https://" + self.BaseHost
        self.timeout = 5
        self.get_constants()
 
        self.sessionUrl = self.BaseURL+"/api/v1/user/oauth2/authorize?response_type=code&state=test&client_id="+self.ServiceId+"&redirect_uri="+self.BaseURL+"/api/v1/user/oauth2/redirect"
        self.loginUrl = self.BaseURL+"/api/v1/user/signin"
        self.languageUrl = self.BaseURL+"/api/v1/user/language"
        self.redirectUri = self.BaseURL+"/api/v1/user/oauth2/redirect"
        self.tokenUrl = self.BaseURL+"/api/v1/user/oauth2/token"
        self.integrationUrl = self.BaseURL+"/api/v1/user/integrationinfo"
        self.silentSignInUrl = self.BaseURL+"/api/v1/user/silentsignin"

        return
    
    @property
    def stamp(self):
        return self.__stamp__

    @stamp.setter
    def stamp(self, stamp):
        self.__stamp__ = stamp
        
    def api_error(self, message):
        logger = logging.getLogger("root")
        logger.error(message)
        print(message)

        # const clientId = "6d477c38-3ca4-4cf3-9557-2a1929a94654";
        # const appId = "014d2225-8495-4735-812d-2616334fd15d";


    def get_constants(self):
        if self.car_brand == "kia":
            self.ServiceId = "fdc85c00-0a2f-4c64-bcb4-2cfb1500730a"
            self.BasicToken = "Basic ZmRjODVjMDAtMGEyZi00YzY0LWJjYjQtMmNmYjE1MDA3MzBhOnNlY3JldA=="
            #self.CcspApplicationId = "693a33fa-c117-43f2-ae3b-61a02d24f417"
            self.CcspApplicationId = "a2b8469b-30a3-4361-8e13-6fceea8fbe74"# app id per July 1st, 2023
        elif self.car_brand == "hyundai":
            self.ServiceId = "6d477c38-3ca4-4cf3-9557-2a1929a94654" #clientId in bluelinky
            self.BasicToken = "Basic NmQ0NzdjMzgtM2NhNC00Y2YzLTk1NTctMmExOTI5YTk0NjU0OktVeTQ5WHhQekxwTHVvSzB4aEJDNzdXNlZYaG10UVI5aVFobUlGampvWTRJcHhzVg=="
            #self.CcspApplicationId = "014d2225-8495-4735-812d-2616334fd15d"
            self.CcspApplicationId = "1eba27d2-9a5b-4eba-8ec7-97eb6c62fb51" # app id per July 1st, 2023
        else:
            self.api_error("Carbrand not OK.")
            return False

        self.UserAgentPreLogon = "Mozilla/5.0 (iPhone; CPU iPhone OS 11_1 like Mac OS X) AppleWebKit/604.3.5 (KHTML, like Gecko) Version/11.0 Mobile/15B92 Safari/604.1"
        self.UserAgent = "UVO_REL/1.5.1 (iPhone; iOS 14.0.1; Scale/2.00)"
        self.UserAgent = "UVO_Store/1.5.9 (iPhone; iOS 14.4; Scale/3.00)"
        self.USER_AGENT_OK_HTTP: str = "okhttp/3.12.0"
        self.Accept = "*/*"
        self.AcceptLanguageShort = "nl-nl"
        self.AcceptLanguage = "nl-NL;q=1, en-NL;q=0.9"
        self.AcceptEncoding = "gzip, deflate, br"
        self.ContentType = "application/x-www-form-urlencoded;charset=UTF-8"
        self.ContentJSON = "application/json;charset=UTF-8"
        self.Connection = "Keep-Alive"
        self.deviceId = ""
        return True

    def check_control_token(self):
        if self.refresh_access_token():
            logging.debug('accesstoken OK')
            if self.controlTokenExpiresAt is not None:
                logging.debug("Check pin expiry on %s and now it is %s", self.controlTokenExpiresAt, datetime.now())
                if self.controlToken is None or datetime.now() > self.controlTokenExpiresAt:
                    logging.debug("control token expired at %s, about to renew", self.controlTokenExpiresAt)
                    return self.enter_pin()
        return True

    def refresh_access_token(self):
        if self.refreshToken is None:
            self.api_error("Need refresh token to refresh access token. Use login()")
            return False
        logging.debug("access token expires at %s", self.accessTokenExpiresAt)
        if (datetime.now() - self.accessTokenExpiresAt).total_seconds() > -3600: #one hour beforehand refresh the access token
            logging.debug("need to refresh access token")
            url = self.BaseURL + "/api/v1/user/oauth2/token"
            headers = {
                "Host": self.BaseHost,
                "Content-type": self.ContentType,
                "Accept-Encoding": self.AcceptEncoding,
                "Connection": self.Connection,
                "Accept": self.Accept,
                "User-Agent": self.UserAgent,
                "Accept-Language": self.AcceptLanguage,
                "Stamp": self.__stamp__,
                "Authorization": self.BasicToken
                }
            logging.debug(headers)
            data = "redirect_uri=" + self.BaseURL + "/api/v1/user/oauth2/redirect&refresh_token=" + self.refreshToken + "&grant_type=refresh_token"
            response = requests.post(url, data=data, headers=headers, timeout=self.timeout)
            logging.debug("refreshed access token %s",response)
            logging.debug("response text %s",json.loads(response.text))
            if response.status_code == 200:
                try:
                    response = json.loads(response.text)
                    self.accessToken = "Bearer " + response["access_token"]
                    self.accessTokenExpiresAt = datetime.now() + timedelta(seconds=response["expires_in"])
                    logging.info("refreshed access token %s expires in %s seconds at %s",
                                 self.accessToken[:40], response["expires_in"], self.accessTokenExpiresAt)

                    return True
                except:
                    self.api_error("Refresh token failed: " + response)
                    return False
            else:
                self.api_error("Refresh token failed: " + str(response.status_code) + response.text)
                return False
        return True

    def enter_pin(self):
        url = self.BaseURL + "/api/v1/user/pin"
        headers = {
            "Host": self.BaseHost,
            "Content-Type": self.ContentType,
            "Accept-Encoding": self.AcceptEncoding,
            "Connection": self.Connection,
            "Accept": self.Accept,
            "User-Agent": self.UserAgent,
            "Accept-Language": self.AcceptLanguage,
            "Stamp": self.__stamp__,
            "Authorization": self.accessToken
        }
        data = {"deviceId": self.deviceId, "pin": self.pin}
        response = requests.put(url, json=data, headers=headers, cookies=self.cookies, timeout=self.timeout)
        if response.status_code == 200:
            try:
                response = json.loads(response.text)
                self.controlToken = "Bearer " + response["controlToken"]
                self.controlTokenExpiresAt = datetime.now() + timedelta(seconds=response["expiresTime"])
                logging.debug("Pin set, new control token %s, expires in %s seconds at %s",
                              self.controlToken[:40], response["expiresTime"], self.controlTokenExpiresAt)
                return True
            except:
                self.api_error("NOK pin. Error: " + response)
                return False
        else:
            self.api_error("NOK pin. Error: " + str(response.status_code) + response.text)
            return False

    def login_legacy(self, email, password, pin, vin):
        self.pin = pin
        url = "no URL set yet"
        logging.info("entering login legacy, car brand:  %s, email: %s", self.car_brand, email)
        #self.get_constants()
        logging.debug("login legacy: constants ServiceId %s BasicToken %s CcspApplicationId %s BaseHost %s BaseURL %s stamp %s", self.ServiceId, self.BasicToken, self.CcspApplicationId, self.BaseHost, self.BaseURL, self.__stamp__)
        self.controlToken = self.accessToken = self.refreshToken = None
        self.controlTokenExpiresAt = self.accessTokenExpiresAt = datetime(1970, 1, 1, 0, 0, 0)

        #try:
        # ---step 1 cookies----------------------------------
        url = self.BaseURL + "/api/v1/user/oauth2/authorize?response_type=code&state=test&client_id=" + self.ServiceId + "&redirect_uri=" + self.BaseURL + "/api/v1/user/oauth2/redirect"
        headers = {
            "Connection": self.Connection,
            "Accept": self.Accept,
            "User-Agent": self.UserAgentPreLogon,
            "Accept-Encoding": self.AcceptEncoding
        }
        session = requests.Session()
        try:
            response = session.get(url, headers=headers, timeout=self.timeout)
        except requests.exceptions.RequestException as exp:
            self.api_error("RequestException: " + str(exp))
            return False
        logging.debug("login legacy URL 1 "+url)
        if response.status_code != 200:
            self.api_error("NOK login legacy: NOK cookie for login. Error: " + str(response.status_code) + response.text)
            return False

        self.cookies = session.cookies.get_dict()
        logging.debug("login legacy cookies: " + str(self.cookies))

        # https: // prd.eu - ccapi.kia.com: 8080 / web / v1 / user / authorize?lang = en & cache = reset
        # https: // prd.eu - ccapi.kia.com: 8080 / web / v1 / user / static / css / main.dbfc71fc.chunk.css
        # https: // prd.eu - ccapi.kia.com: 8080 / web / v1 / user / static / js / 2.cf048054.chunk.js
        # https: // prd.eu - ccapi.kia.com: 8080 / web / v1 / user / static / js / main.b922ef51.chunk.js

        # ---step 2 language----------------------------------
        headers = {
            "Content-Type": "text/plain",
            "Connection": self.Connection,
            "Accept": self.Accept,
            "User-Agent": self.UserAgentPreLogon
        }
        data = {"lang": "en"}
        logging.debug("login legacy headers 2 "+str(headers))
        logging.debug("login legacy data 2 "+str(data))
        url = self.BaseURL + "/api/v1/user/language"
        logging.debug("login legacy URL 2 "+url)
        try:
            response = requests.post(url, json=data, headers=headers, cookies=self.cookies, timeout=self.timeout)
        except requests.exceptions.RequestException as exp:
            self.api_error("RequestException: " + str(exp))
            return False
        if response.status_code >= 300:
            self.api_error("NOK login legacy: NOK set language for login. Error: " + str(response.status_code) + response.text)
            return False
        else:
            logging.debug("login legacy language set OK")

        # --- step 3 signin----------------------------------
        url = self.BaseURL + "/api/v1/user/signin"
        headers = {
            "Content-Type": self.ContentJSON,
            "User-Agent": self.UserAgent,
            "Accept": self.Accept,
            "Connection": self.Connection
        }
        data = {"email": email, "password": password}
        logging.debug("login URL 3 "+url)
        logging.debug("login headers 3 "+str(headers))
        logging.debug("login data 3 "+str(data))
        try:
            response = requests.post(url, json=data, headers=headers, cookies=self.cookies, timeout=self.timeout)
        except requests.exceptions.RequestException as exp:
            self.api_error("RequestException: " + str(exp))
            return False
        if response.status_code != 200:
            self.api_error("NOK login. Error: " + str(response.status_code) + " " + response.text)
            return False
        try:
            response = json.loads(response.text)
            response = response["redirectUrl"]
            parsed = urlparse.urlparse(response)
            authcode = "".join(parse_qs(parsed.query)["code"])
            logging.debug("authCode %s", authcode)
        except:
            self.api_error("NOK login. Error in parsing /signing request " + response)
            return False

        # ---step 4 get accesstoken----------------------------------
        url = self.BaseURL + "/api/v1/user/oauth2/token"
        headers = {
            "ccsp-service-id": self.ServiceId,
            "Host": self.BaseHost,
            "Content-Type": self.ContentType,
            "Accept-Encoding": self.AcceptEncoding,
            "Connection": self.Connection,
            "Accept": self.Accept,
            "User-Agent": self.UserAgent,
            "Accept-Language": self.AcceptLanguage,
            "ccsp-application-id": self.CcspApplicationId,
            "Stamp": self.__stamp__,
            "Authorization": self.BasicToken
        }

        data = "grant_type=authorization_code&redirect_uri=" + self.BaseURL + "/api/v1/user/oauth2/redirect&code=" + authcode
        logging.debug("login URL 4 "+url)
        logging.debug("login headers 4 "+str(headers))
        logging.debug("login data 4 "+str(data))
        try:
            response = requests.post(url, data=data, headers=headers, cookies=self.cookies, timeout=self.timeout)
        except requests.exceptions.RequestException as exp:
            self.api_error("RequestException: " + str(exp))
            return False
        if response.status_code != 200:
            self.api_error("NOK token. Error: " + str(response.status_code) + " " + response.text)
            return False
        try:
            response = json.loads(response.text)
            self.accessToken = "Bearer " + response["access_token"]
            self.refreshToken = response["refresh_token"]
            self.accessTokenExpiresAt = datetime.now() + timedelta(seconds=response["expires_in"])
            logging.info("accesstoken %s, refrestoken %s expiresAt %s", self.accessToken, self.refreshToken, self.accessTokenExpiresAt)
        except:
            self.api_error("NOK login. Error in parsing /token request: " + response)
            return False
        # notification/register

        # # --- step 5 get deviceid----------------------------------
        url = self.BaseURL + "/api/v1/spa/notifications/register"
        headers = {
            "ccsp-service-id": self.ServiceId,
            "cssp-application-id": self.CcspApplicationId,
            "Content-Type": self.ContentJSON,
            "Host": self.BaseHost,
            "Connection": self.Connection,
            "Accept-Encoding": self.AcceptEncoding,
            "Stamp": self.__stamp__,
            "User-Agent": self.UserAgent}
        # what to do with the cookie? account=Nj<snip>>689c3 
        # what to do with the right PushRegId
        data = {"pushRegId": "0827a4e6c94faa094fe20033ff7fdbbd3a7a789727546f2645a0f547f5db2a58", "pushType": "APNS", "uuid": str(uuid.uuid1())}
        logging.debug("login URL 5 "+url)
        logging.debug("login headers 5 "+str(headers))
        logging.debug("login data 5 "+str(data))
        try:
            response = requests.post(url, json=data, headers=headers, timeout=self.timeout)
        except requests.exceptions.RequestException as exp:
            self.api_error("RequestException: " + str(exp))
            return False
        if response.status_code != 200:
            self.api_error("NOK login: NOK deviceID. Error: " + str(response.status_code) + " " + response.text)
            logging.debug("the rescode = " + response.json()["resCode"])
            if response.json()["resCode"] == "4017":
                raise StampInvalid
            return False
        else:
            logging.debug("OK login: OK deviceID, message: " + str(response.status_code) + " " + response.text)
        try:
            response = json.loads(response.text)
            self.deviceId = response["resMsg"]["deviceId"]
            logging.debug("deviceId %s", self.deviceId)
        except:
            self.api_error("NOK login: Error in parsing /signing request: " + response)
            return False

        # user/profile    --> toevoegen bluelinky?
        # setting/language --> toevoegen bluelinky?
        # setting/service --> toevoegen bluelinky?


        # vehicles

        # ---step 6 get vehicles----------------------------------
        url = self.BaseURL + "/api/v1/spa/vehicles"
        headers = {
            "Host": self.BaseHost,
            "Accept": self.Accept,
            "Authorization": self.accessToken,
            "ccsp-application-id": self.CcspApplicationId,
            "Accept-Encoding": "gzip",
            "User-Agent": "okhttp/3.10.0",
            "offset": "2",
            "Connection": self.Connection,
            "Content-Type": self.ContentJSON,
            "Stamp": self.__stamp__,
            "ccsp-device-id": self.deviceId
        }
        try:
            response = requests.get(url, headers=headers, cookies=self.cookies, timeout=self.timeout)
        except requests.exceptions.RequestException as exp:
            self.api_error("RequestException: " + str(exp))
            return False
        logging.debug("login URL 6 "+url)
        logging.debug("login headers 6 "+str(headers))
        if response.status_code != 200:
            self.api_error("NOK vehicles. Error: " + str(response.status_code) + " " + response.text)
            return False
        try:
            response = json.loads(response.text)
            logging.debug("response %s", response)
            vehicles = response["resMsg"]["vehicles"]
            logging.debug("%s vehicles found", len(vehicles))
        except:
            self.api_error("NOK login. Error in getting vehicles: " + response)
            return False
        if len(vehicles) == 0:
            self.api_error("NOK login. No vehicles found")
            return False
        # ---get vehicleId----------------------------------
        self.vehicleId = None
        if len(vehicles) > 1:
            for vehicle in vehicles:
                url = self.BaseURL + "/api/v1/spa/vehicles/" + vehicle["vehicleId"] + "/profile"
                headers = {
                    "Host": self.BaseHost,
                    "Accept": self.Accept,
                    "Authorization": self.accessToken,
                    "ccsp-application-id": self.CcspApplicationId,
                    "Accept-Language": self.AcceptLanguage,
                    "Accept-Encoding": self.AcceptEncoding,
                    "offset": "2",
                    "User-Agent": self.UserAgent,
                    "Connection": self.Connection,
                    "Content-Type": self.ContentJSON,
                    "Stamp": self.__stamp__,
                    "ccsp-device-id": self.deviceId
                }
                logging.debug("login URL 7 "+url)
                logging.debug("login headers 7 "+str(headers))
                try:
                    response = requests.get(url, headers=headers, cookies=self.cookies, timeout=self.timeout)
                except requests.exceptions.RequestException as exp:
                    self.api_error("RequestException: " + str(exp))
                    return False
                try:
                    response = json.loads(response.text)
                    response = response["resMsg"]["vinInfo"][0]["basic"]
                    vehicle["vin"] = response["vin"]
                    vehicle["generation"] = response["modelYear"]
                except:
                    self.api_error("NOK login. Error in getting profile of vehicle: " + vehicle + " " + response)
                    return False
                if vehicle["vin"] == vin: self.vehicleId = vehicle["vehicleId"]
            if self.vehicleId is None:
                self.api_error("NOK login. The VIN you entered is not in the vehicle list " + vin)
                return False
        else: self.vehicleId = vehicles[0]["vehicleId"]
        logging.debug("vehicleID %s", self.vehicleId)
        # the normal startup routine of the app is
        # profile
        # register
        # records
        # dezemoeten niet met de control token maar nog met de access token, te complex om te implementeren
        # api_get_services()
        # api_get_status(False)
        # api_get_parklocation()
        # self.api_set_wakeup()
        # api_get_valetmode()
        # api_get_finaldestination()
        logging.info("Finished successfull login_legacy procedure")
        return True

    def get_cookies (self):
        url = self.BaseURL + "/api/v1/user/oauth2/authorize?response_type=code&client_id=" + self.ServiceId + "&redirect_uri=" + self.BaseURL + "/api/v1/user/oauth2/redirect&state=test&lang=en"
        session = requests.Session()
        response = session.get(url)
        logging.debug("login URL 1 "+url)
        if response.status_code != 200:
            self.api_error("NOK login: NOK cookie for login. Error: " + str(response.status_code) + response.text)
            return False

        self.cookies = session.cookies.get_dict()

    def get_device_id(self):
        url = self.BaseURL + "/api/v1/spa/notifications/register"
        registration_id = 1
        theUid = str(uuid.uuid4())
        payload = {
            "pushRegId": registration_id,
            "pushType": "GCM",
            "uuid": theUid,
        }
 
        headers = {
            "ccsp-service-id": self.ServiceId,
            "ccsp-application-id": self.CcspApplicationId,
            "Stamp": self.__stamp__,
            "Content-Type": self.ContentJSON,
        }

        response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        logging.debug(f"Get Device ID request: {headers} {payload} ")
        logging.debug(f"Get Device ID response: {response} {response.encoding} {response.headers} {response.url}")
        orig_req = response.request

        if response.status_code != 200:
            self.api_error("NOK login: NOK deviceID. Error: " + str(response.status_code) + " " + response.text)
            return False
        try:
            response = json.loads(response.text)
            self.deviceId = response["resMsg"]["deviceId"]
            logging.debug("deviceId %s", self.deviceId)
        except:
            self.api_error("NOK login: Error in parsing /signing request: " + response)
            return False
        return response

    def set_language(self, lang="en"):
        url = self.languageUrl # "/api/v1/user/language"
        headers = {
            "Host": self.BaseHost,
            "Content-Type": self.ContentJSON,
            "Origin": self.BaseURL,
            "Connection": self.Connection,
            "Accept": self.Accept,
            "User-Agent": self.UserAgentPreLogon,
            "Referer": self.BaseURL + "/web/v1/user/authorize?lang=en&cache=reset",
            "Accept-Language": self.AcceptLanguageShort,
            "Accept-Encoding": self.AcceptEncoding
        }
        data = {"lang": str(lang)}
        logging.debug("language URL "+url+" headers "+str(headers)+" data "+str(data))
        requests.post(url, json=data, headers=headers, cookies=self.cookies, timeout=self.timeout)

    def login_brand(self, email, password, pin, vin):
        self.pin = pin
        url = "no URL set yet"
        logging.info("entering login, car brand:  %s, email: %s", self.car_brand, email)
        #self.get_constants()
        logging.debug("login: constants %s %s %s %s %s %s", self.ServiceId, self.BasicToken, self.CcspApplicationId, self.BaseHost, self.BaseURL, self.__stamp__)
        self.controlToken = self.accessToken = self.refreshToken = None
        self.controlTokenExpiresAt = self.accessTokenExpiresAt = datetime(1970, 1, 1, 0, 0, 0)

        # try
        # ---get deviceid----------------------------------
        if self.get_device_id() == False:
            return False
        # ---cookies----------------------------------
        self.get_cookies()
        # --- set language----------------------------------
        self.set_language("nl")

        # ---signin----------------------------------
        url = self.BaseURL + "/api/v1/user/signin"
        headers = {
            "Host": self.BaseHost,
            "Content-Type": self.ContentJSON,
            "Origin": self.BaseURL,
            "Connection": self.Connection,
            "Accept": self.Accept,
            "User-Agent": self.UserAgentPreLogon,
            "Referer": self.BaseURL+"/web/v1/user/signin",
            "Accept-Language": self.AcceptLanguageShort,
            "Stamp": self.__stamp__,
            "Accept-Encoding": self.AcceptEncoding
        }
        data = {"email": email, "password": password}
        logging.debug("sign in URL "+url+" headers "+str(headers)+" data "+str(data))
        response = requests.post(url, json=data, headers=headers, cookies=self.cookies, timeout=self.timeout)
        if response.status_code != 200:
            self.api_error("NOK login. Error: " + str(response.status_code) + " " + response.text)
            return False
        try:
            response = json.loads(response.text)
            response = response["redirectUrl"]
            parsed = urlparse.urlparse(response)
            authcode = "".join(parse_qs(parsed.query)["code"])
            logging.debug("authCode %s", authcode)
        except:
            self.api_error("NOK login. Error in parsing /signing request " + response)
            return False

        # ---get accesstoken----------------------------------
        url = self.BaseURL + "/api/v1/user/oauth2/token"
        headers = {
            "Host": self.BaseHost,
            "Content-Type": self.ContentType,
            "Accept-Encoding": self.AcceptEncoding,
            "Connection": self.Connection,
            "Accept": self.Accept,
            "User-Agent": self.UserAgent,
            "Accept-Language": self.AcceptLanguage,
            "Stamp": self.__stamp__,
            "Authorization": self.BasicToken
        }
        data = "redirect_uri=" + self.BaseURL + "/api/v1/user/oauth2/redirect&code=" + authcode + "&grant_type=authorization_code"
        logging.debug("get token URL "+url+" headers "+str(headers)+" data "+str(data))
        response = requests.post(url, data=data, headers=headers, cookies=self.cookies, timeout=self.timeout)
        if response.status_code != 200:
            self.api_error("NOK token. Error: " + str(response.status_code) + " " + response.text)
            return False
        try:
            response = json.loads(response.text)
            self.accessToken = "Bearer " + response["access_token"]
            self.refreshToken = response["refresh_token"]
            self.accessTokenExpiresAt = datetime.now() + timedelta(seconds=response["expires_in"])
            logging.debug("accesstoken %s, refrestoken %s expiresAt %s", self.accessToken, self.refreshToken, self.accessTokenExpiresAt)
        except:
            self.api_error("NOK login. Error in parsing /token request: " + response)
            return False
        # notification/register


        # ---get vehicles----------------------------------
        url = self.BaseURL + "/api/v1/spa/vehicles"
        headers = {
            "Host": self.BaseHost,
            "Accept": self.Accept,
            "Authorization": self.accessToken,
            "ccsp-application-id": self.CcspApplicationId,
            "Accept-Language": self.AcceptLanguage,
            "Accept-Encoding": self.AcceptEncoding,
            "offset": "2",
            "User-Agent": self.UserAgent,
            "Connection": self.Connection,
            "Content-Type": self.ContentJSON,
            "Stamp": self.__stamp__,
            "ccsp-device-id": self.deviceId
        }

        try:
            response = requests.get(url, headers=headers, cookies=self.cookies, timeout=self.timeout)
        except requests.exceptions.RequestException as exp:
            self.api_error("Login RequestException: " + str(exp))
            return False
        logging.debug("get vehicles URL "+url+" headers "+str(headers)+" data none")
        if response.status_code != 200:
            self.api_error("NOK vehicles. Error: " + str(response.status_code) + " " + response.text)
            return False
        try:
            response = json.loads(response.text)
            logging.debug("response %s", response)
            vehicles = response["resMsg"]["vehicles"]
            logging.debug("%s vehicles found", len(vehicles))
        except:
            self.api_error("NOK login. Error in getting vehicles: " + response)
            return False
        if len(vehicles) == 0:
            self.api_error("NOK login. No vehicles found")
            return False
        # ---get vehicleId----------------------------------
        self.vehicleId = None
        if len(vehicles) > 1:
            for vehicle in vehicles:
                url = self.BaseURL + "/api/v1/spa/vehicles/" + vehicle["vehicleId"] + "/profile"
                headers = {
                    "Host": self.BaseHost,
                    "Accept": self.Accept,
                    "Authorization": self.accessToken,
                    "ccsp-application-id": self.CcspApplicationId,
                    "Accept-Language": self.AcceptLanguage,
                    "Accept-Encoding": self.AcceptEncoding,
                    "offset": "2",
                    "User-Agent": self.UserAgent,
                    "Connection": self.Connection,
                    "Content-Type": self.ContentJSON,
                    "Stamp": self.__stamp__,
                    "ccsp-device-id": self.deviceId
                }
                logging.debug("get vehicle ID URL "+url+" headers "+str(headers)+" data none")
                response = requests.get(url, headers=headers, cookies=self.cookies, timeout=self.timeout)
                try:
                    response = json.loads(response.text)
                    response = response["resMsg"]["vinInfo"][0]["basic"]
                    vehicle["vin"] = response["vin"]
                    vehicle["generation"] = response["modelYear"]
                except:
                    self.api_error("NOK login. Error in getting profile of vehicle: " + vehicle + " " + response)
                    return False
                if vehicle["vin"] == vin: self.vehicleId = vehicle["vehicleId"]
            if self.vehicleId is None:
                self.api_error("NOK login. The VIN you entered is not in the vehicle list " + vin)
                return False
        else: self.vehicleId = vehicles[0]["vehicleId"]
        logging.debug("vehicleID %s", self.vehicleId)
        # except:
            # self.api_error("Login failed. URL: '"+ url + "', response: '" + response.text)
            # return False
        # the normal startup routine of the app is
        # profile
        # register
        # records
        # dezemoeten niet met de control token maar nog met de access token, te complex om te implementeren
        # api_get_services()
        # api_get_status(False)
        # api_get_parklocation()
        # self.api_set_wakeup()
        # api_get_valetmode()
        # api_get_finaldestination()
        logging.info("Finished successfull login procedure")
        return True

    def defaultHeaders(self):
        return {
            "Authorization": self.accessToken,
            #"offset": (new Date().getTimezoneOffset() / 60).toFixed(2),
            "offset": "2",
            "ccsp-device-id": self.deviceId,
            "ccsp-application-id": self.CcspApplicationId,
            "Content-Type": "application/json"
        }

class vehicleInteraction(brandAuth):
        
    def api_get_valetmode(self):
        url = self.BaseURL + "/api/v1/spa/vehicles/" + self.vehicleId + "/status/valet"
        headers = {
            "Host": self.BaseHost,
            "Accept": self.Accept,
            "Authorization": self.accessToken,
            "ccsp-application-id": self.CcspApplicationId,
            "Accept-Language": self.AcceptLanguage,
            "Accept-Encoding": self.AcceptEncoding,
            "offset": "2",
            "User-Agent": self.UserAgent,
            "Connection": self.Connection,
            "Content-Type": self.ContentJSON,
            "Stamp": self.__stamp__,
            "ccsp-device-id": self.deviceId
        }
        response = requests.get(url, headers=headers, cookies=self.cookies, timeout=self.timeout)
        if response.status_code == 200:
            try:
                response = json.loads(response.text)
                return response['resMsg']['valetMode']
            except ValueError:
                self.api_error('NOK Parsing valetmode: ' + response)
                return False
        else:
            self.api_error('NOK requesting valetmode. Error: ' + str(response.status_code) + response.text)
            return False

    def api_get_parklocation(self):
        url = self.BaseURL + '/api/v1/spa/vehicles/' + self.vehicleId + '/location/park'
        headers = {
            'Host': self.BaseHost,
            'Accept': self.Accept,
            'Authorization': self.accessToken,
            'ccsp-application-id': self.CcspApplicationId,
            'Accept-Language': self.AcceptLanguage,
            'Accept-Encoding': self.AcceptEncoding,
            'offset': '2',
            'User-Agent': self.UserAgent,
            'Connection': self.Connection,
            'Content-Type': self.ContentJSON,
            'Stamp': self.__stamp__,
            'ccsp-device-id': self.deviceId
        }
        response = requests.get(url, headers=headers, cookies=self.cookies, timeout=self.timeout)
        if response.status_code == 200:
            try:
                response = json.loads(response.text)
                return response['resMsg']
            except ValueError:
                self.api_error('NOK Parsing location park: ' + response)
                return False
        else:
            self.api_error('NOK requesting location park. Error: ' + str(response.status_code) + response.text)
            return False

    def api_get_finaldestination(self):
        url = self.BaseURL + '/api/v1/spa/vehicles/' + self.vehicleId + '/finaldestionation'
        headers = {
            'Host': self.BaseHost,
            'Accept': self.Accept,
            'Authorization': self.accessToken,
            'ccsp-application-id': self.CcspApplicationId,
            'Accept-Language': self.AcceptLanguage,
            'Accept-Encoding': self.AcceptEncoding,
            'offset': '2',
            'User-Agent': self.UserAgent,
            'Connection': self.Connection,
            'Content-Type': self.ContentJSON,
            'Stamp': self.__stamp__,
            'ccsp-device-id': self.deviceId
        }
        response = requests.get(url, headers=headers, cookies=self.cookies, timeout=self.timeout)
        if response.status_code == 200:
            try:
                response = json.loads(response.text)
                return response['resMsg']
            except ValueError:
                self.api_error('NOK Parsing final destination: ' + response)
                return False
        else:
            self.api_error('NOK requesting final destination. Error: ' + str(response.status_code) + response.text)
            return False

    def api_set_wakeup(self):
        url = self.BaseURL + '/api/v1/spa/vehicles/' + self.vehicleId + '/control/engine'
        headers = {
            'Host': self.BaseHost,
            'Accept': self.Accept,
            'Authorization': self.accessToken,
            'Accept-Encoding': self.AcceptEncoding,
            'ccsp-application-id': self.CcspApplicationId,
            'Accept-Language': self.AcceptLanguage,
            'offset': '2',
            'User-Agent': self.UserAgent,
            'Connection': self.Connection,
            'Content-Type': self.ContentJSON,
            'Stamp': self.__stamp__,
            'ccsp-device-id': self.deviceId
        }
        data = {"action": "prewakeup", "deviceId": self.deviceId}
        response = requests.post(url, json=data, headers=headers, timeout=self.timeout)
        if response.status_code == 200:
            return True
        else:
            self.api_error('NOK prewakeup. Error: ' + str(response.status_code) + response.text)
            return False

    def api_get_status(self, refresh=False, raw=True):
        logging.debug('into get status')
        # get status either from cache or not
        if not self.check_control_token(): return False
        logging.debug('checked control token')
        cachestring = '' if refresh else '/latest'
        timeout = self.timeout*6 if refresh else self.timeout #a refresh takes more time so the standard timeout may not be long enough
        url = self.BaseURL + '/api/v2/spa/vehicles/' + self.vehicleId + '/status' + cachestring
        headers = {
            'Host': self.BaseHost, 'Accept': self.Accept, 'Authorization': self.controlToken,
            'ccsp-application-id': self.CcspApplicationId,
            'Accept-Language': self.AcceptLanguage, 'Accept-Encoding': self.AcceptEncoding, 'offset': '2',
            'Stamp': self.__stamp__,
            'User-Agent': self.UserAgent, 'Connection': self.Connection, 'Content-Type': self.ContentJSON, 'ccsp-device-id': self.deviceId
        }
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
        except requests.exceptions.ReadTimeout:
            self.api_error("Timeout: failed to get status.")
            return False
            
        logging.debug('got status')
        if response.status_code == 200:
            try:
                response = json.loads(response.text)
                # a refresh==True returns a short list, a refresh==False returns a long list. If raw is true, return the entire string
                logging.debug("get status response: " + str(response['resMsg']))
                if raw: return response['resMsg']
                if not refresh: response = response['resMsg']['vehicleStatusInfo']['vehicleStatus']
                return response
            except requests.exceptions.RequestException as exp:
                self.api_error("RequestException: " + str(exp))
            except:
                self.api_error('NOK parsing status: ' + response)
                return False
        else:
            self.api_error('NOK requesting status. Error: ' + str(response.status_code) + response.text)
            return False

    def api_get_odometer(self):
        if not self.check_control_token(): return False
        # odometer
        url = self.BaseURL + '/api/v2/spa/vehicles/' + self.vehicleId + '/status/latest'
        headers = {
            'Host': self.BaseHost, 'Accept': self.Accept, 'Authorization': self.controlToken,
            'ccsp-application-id': self.CcspApplicationId,
            'Accept-Language': self.AcceptLanguage, 'Accept-Encoding': self.AcceptEncoding, 'offset': '2',
            'Stamp': self.__stamp__,
            'User-Agent': self.UserAgent, 'Connection': self.Connection, 'Content-Type': self.ContentJSON, 'ccsp-device-id': self.deviceId
        }
        response = requests.get(url, headers=headers, timeout=self.timeout)
        if response.status_code == 200:
            try:
                response = json.loads(response.text)
                return response['resMsg']['vehicleStatusInfo']['odometer']['value']
            except ValueError:
                self.api_error('NOK Parsing odometer: ' + response)
                return False
        else:
            self.api_error('NOK requesting odometer. Error: ' + str(response.status_code) + response.text)
            return False

    def api_get_location(self):
        if not self.check_control_token(): return False
        # location
        url = self.BaseURL + '/api/v2/spa/vehicles/' + self.vehicleId + '/location'
        headers = {
            'Host': self.BaseHost, 'Accept': self.Accept, 'Authorization': self.controlToken,
            'ccsp-application-id': self.CcspApplicationId,
            'Accept-Language': self.AcceptLanguage, 'Accept-Encoding': self.AcceptEncoding, 'offset': '2',
            'Stamp': self.__stamp__,
            'User-Agent': self.UserAgent, 'Connection': self.Connection, 'Content-Type': self.ContentJSON, 'ccsp-device-id': self.deviceId
        }

        response = requests.get(url, headers=headers, timeout=self.timeout)
        if response.status_code == 200:
            try:
                response = json.loads(response.text)
                return response['resMsg']
            except ValueError:
                self.api_error('NOK Parsing location: ' + response)
                return False
        else:
            self.api_error('NOK requesting location. Error: ' + str(response.status_code) + response.text)
            return False

    def api_set_lock(self, action='close'):
        logging.debug("set lock: action='"+action+ "'")
        if action == "":
            self.api_error('NOK Emtpy lock parameter')
            return False
        if type(action) == bool:
            if action:
                action = 'close'
            else:
                action = 'open'
        else:
            action = str.lower(action)
            if action == 'on': action = 'close'
            if action == 'lock': action = 'close'
            if action == 'off': action = 'open'
        if not (action == 'close' or action == 'open'):
            self.api_error('NOK Invalid locking parameter')
            return False

        if not self.check_control_token(): return False

        # location
        url = self.BaseURL + '/api/v2/spa/vehicles/' + self.vehicleId + '/control/door'
        headers = {
            'Host': self.BaseHost, 'Accept': self.Accept, 'Authorization': self.controlToken,
            'ccsp-application-id': self.CcspApplicationId,
            'Accept-Language': self.AcceptLanguage, 'Accept-Encoding': self.AcceptEncoding, 'offset': '2',
            'Stamp': self.__stamp__,
            'User-Agent': self.UserAgent, 'Connection': self.Connection, 'Content-Type': self.ContentJSON, 'ccsp-device-id': self.deviceId
        }

        data = {"deviceId": self.deviceId, "action": action}
        response = requests.post(url, json=data, headers=headers, timeout=self.timeout)
        if response.status_code == 200:
            logging.debug("Send (un)lock command to Vehicle")
            return True
        else:
            self.api_error('Error sending lock. Error: ' + str(response.status_code)  + response.text)
            return False

    def api_set_charge(self, action='stop'):
        if action == "":
            self.api_error('NOK Emtpy charging parameter')
            return False
        if type(action) == bool:
            if action:
                action = 'start'
            else:
                action = 'stop'
        else:
            action = str.lower(action)
            if action == 'on': action = 'start'
            if action == 'off': action = 'stop'
        if not (action == 'start' or action == 'stop'):
            self.api_error('NOK Invalid charging parameter')
            return False
        if not self.check_control_token(): return False
        # location
        url = self.BaseURL + '/api/v2/spa/vehicles/' + self.vehicleId + '/control/charge'
        headers = {
            'Host': self.BaseHost, 'Accept': self.Accept, 'Authorization': self.controlToken,
            'ccsp-application-id': self.CcspApplicationId,
            'Accept-Language': self.AcceptLanguage, 'Accept-Encoding': self.AcceptEncoding, 'offset': '2',
            'Stamp': self.__stamp__,
            'User-Agent': self.UserAgent, 'Connection': self.Connection, 'Content-Type': self.ContentJSON, 'ccsp-device-id': self.deviceId
        }

        data = {"deviceId": self.deviceId, "action": action}
        response = requests.post(url, json=data, headers=headers, timeout=self.timeout)
        if response.status_code == 200:
            logging.debug("Send (stop) charge command to Vehicle")
            return True
        else:
            self.api_error('Error sending start/stop charge. Error: ' + str(response.status_code) + response.text)
            return False

    def api_set_hvac(self, action='stop', temp='21.0', bdefrost=False, bheating=False):
        logging.debug("set hvac: action='"+action+ "', temp='"+temp+"', bdefrost='"+str(bdefrost)+"', bheating='"+str(bheating)+"'")
        if action == "":
            self.api_error('NOK Emtpy HVAC parameter')
            return False
        if type(action) == bool:
            if action:
                action = 'start'
            else:
                action = 'stop'
        else:
            action = str.lower(action)
            if action == 'on': action = 'start'
            if action == 'off': action = 'stop'
        if not (action == 'stop' or action == 'start'):
            self.api_error('NOK Invalid HVAC parameter')
            return False
        try:
            tempcode = temp2hex(temp)
        except:
            tempcode = "0EH"  # default 21 celcius
        try:
            heating = 1 if bheating else 0
        except:
            heating = 1

        if not self.check_control_token(): return False
        # location
        url = self.BaseURL + '/api/v2/spa/vehicles/' + self.vehicleId + '/control/temperature'
        headers = {
            'Host': self.BaseHost, 'Accept': self.Accept, 'Authorization': self.controlToken,
            'ccsp-application-id': self.CcspApplicationId,
            'Accept-Language': self.AcceptLanguage, 'Accept-Encoding': self.AcceptEncoding, 'offset': '2',
            'Stamp': self.__stamp__,
            'User-Agent': self.UserAgent, 'Connection': self.Connection, 'Content-Type': self.ContentJSON, 'ccsp-device-id': self.deviceId
        }
        data = {
            "deviceId": self.deviceId,
            "action": action,
            "hvacType": 1,
            "options": {
                "defrost": bdefrost,
                "heating1": heating
            },
            "unit": 'C',
            "tempCode": tempcode
        }
        response = requests.post(url, json=data, headers=headers, timeout=self.timeout)
        if response.status_code == 200:
            logging.debug("Send HVAC setting to Vehicle")
            return True
        else:
            self.api_error('Error sending HVAC settings. Error: ' + str(response.status_code) + response.text)
            return False

    # ------------ tests -----------
    def api_get_chargeschedule(self):
        if not self.check_control_token(): return False
        # location
        url = self.BaseURL + '/api/v2/spa/vehicles/' + self.vehicleId + '/reservation/charge'
        headers = {
            'Host': self.BaseHost, 'Accept': self.Accept, 'Authorization': self.controlToken,
            'ccsp-application-id': self.CcspApplicationId,
            'Accept-Language': self.AcceptLanguage, 'Accept-Encoding': self.AcceptEncoding, 'offset': '2',
            'Stamp': self.__stamp__,
            'User-Agent': self.UserAgent, 'Connection': self.Connection, 'Content-Type': self.ContentJSON, 'ccsp-device-id': self.deviceId
        }
        response = requests.get(url, headers=headers, timeout=self.timeout)
        if response.status_code == 200:
            try:
                response = json.loads(response.text)
                return response['resMsg']
            except ValueError:
                self.api_error('NOK Parsing charge schedule: ' + response)
        else:
            self.api_error('NOK requesting charge schedule. Error: ' + str(response.status_code) + response.text)
        return False


    def api_set_chargeschedule(self, schedule1, schedule2, tempset, chargeschedule):
        '''
         Parameters Schedule1, Schedule2 = timeschedules for the temperature set
           first array [x,y,z, etc] with x,y,z, days that need to be set, where sunday = 0 and saturday = 6
           second the time and timesection in 12h notation, int or string, plus 0 or 1 (=AM or PM), int or string
           eg [[2,5,6],["1040","0"]] means 10:40 AM on Tuesday, Friday, Saturday

         Param Tempset
          first the temp to be set (in celcius), float or string
          second True or False for defrost on or off
          [23.0, True] means a temperature of 23 celsius and defrosting on

         ChargeSchedule
           first starttime = array time (int or string) and timesection 0 or 1 (AM or PM)
           then  endtime = array time (int or string) and timesection 0 or 1 (AM or PM)
           prio = 1 (only off-peak times) or 2 (prio to off-peak times)
         [["1100","1"],["0700","0"], 1 ] means off peak times are from 23:00 to 07:00 and car should only charge during these off peak times

         if any parameter = True or None, then ignore values. If parameter = False then disable the schedule, else set the values.
        '''
        if not self.check_control_token(): return False

        # first get the currens settings
        data = api_get_chargeschedule()
        olddata = data
        if not (not data):
            try:
                # now enter the new settings

                if not (schedule1 is None or schedule1 is True):  # ignore it of True or None
                    if schedule1 is False:  # turn the schedule off
                        data['reservChargeInfo']['reservChargeInfoDetail']['reservChargeSet'] = False
                    else:
                        data['reservChargeInfo']['reservChargeInfoDetail']['reservChargeSet'] = True
                        schedule = {"day": schedule1[0], "time": {"time": str(schedule1[1][0]), "timeSection": int(schedule1[2][1])}}
                        data['reservChargeInfo']['reservChargeInfoDetail']['reservInfo'] = schedule
                if not (schedule2 is None or schedule2 is True):  # ignore it of True or None
                    if schedule2 is False:  # turn the schedule off
                        data['reservChargeInfo2']['reservChargeInfoDetail']['reservChargeSet'] = False
                    else:
                        data['reservChargeInfo2']['reservChargeInfoDetail']['reservChargeSet'] = True
                        schedule = {"day": schedule2[0], "time": {"time": str(schedule2[1][0]), "timeSection": int(schedule2[2][1])}}
                        data['reservChargeInfo2']['reservChargeInfoDetail']['reservInfo'] = schedule

                if not (tempset is None or tempset is True):  # ignore it of True or None
                    if tempset is False:  # turn the schedule off
                        data['reservChargeInfo']['reservChargeInfoDetail']['reservFatcSet']['airCtrl'] = 0
                        data['reservChargeInfo2']['reservChargeInfoDetail']['reservFatcSet']['airCtrl'] = 0
                    else:
                        data['reservChargeInfo']['reservChargeInfoDetail']['reservFatcSet']['airCtrl'] = 1
                        data['reservChargeInfo2']['reservChargeInfoDetail']['reservFatcSet']['airCtrl'] = 1
                        data['reservChargeInfo']['reservChargeInfoDetail']['reservFatcSet']['airTemp']['value'] = temp2hex(str(tempset[0]))
                        data['reservChargeInfo2']['reservChargeInfoDetail']['reservFatcSet']['airTemp']['value'] = temp2hex(str(tempset[0]))
                        data['reservChargeInfo']['reservChargeInfoDetail']['reservFatcSet']['defrost'] = tempset[1]
                        data['reservChargeInfo2']['reservChargeInfoDetail']['reservFatcSet']['defrost'] = tempset[1]

                if not (chargeschedule is None or chargeschedule is True):  # ignore it of True or None
                    if chargeschedule is False:  # turn the schedule off
                        data['reservFlag'] = 0
                    else:
                        data['reservFlag'] = 1
                        data['offPeakPowerInfo']['offPeakPowerTime1'] = {
                            "starttime": {"time": str(chargeschedule[0][1]), "timeSection": int(chargeschedule[0][1])},
                            "endtime": {"time": str(chargeschedule[1][1]), "timeSection": int(chargeschedule[1][1])}}
                        data['offPeakPowerInfo']['offPeakPowerFlag'] = int(chargeschedule[2])
                if data == olddata: return True  # nothing changed

                url = self.BaseURL + '/api/v2/spa/vehicles/' + self.vehicleId + '/reservation/charge'
                headers = {
                    'Host': self.BaseHost, 'Accept': self.Accept, 'Authorization': self.controlToken,
                    'ccsp-application-id': self.CcspApplicationId,
                    'Accept-Language': self.AcceptLanguage, 'Accept-Encoding': self.AcceptEncoding, 'offset': '2',
                    'User-Agent': self.UserAgent, 'Connection': self.Connection, 'Content-Type': self.ContentJSON,
                    'Stamp': self.__stamp__,
                    'ccsp-device-id': self.deviceId
                }
                data['deviceId'] = self.deviceId
                response = requests.post(url, json=data, headers=headers, timeout=self.timeout)
                if response.status_code == 200: return True
            except:
                self.api_error('NOK setting charge schedule.')
                return False
        self.api_error('NOK setting charge schedule.')
        return False


    def api_set_chargelimits(self, limit_fast=80, limit_slow=100):
        if not self.check_control_token(): return False
        url = self.BaseURL + '/api/v2/spa/vehicles/' + self.vehicleId + '/charge/target'
        headers = {
            'Host': self.BaseHost, 'Accept': self.Accept, 'Authorization': self.controlToken,
            'ccsp-application-id': self.CcspApplicationId,
            'Accept-Language': self.AcceptLanguage, 'Accept-Encoding': self.AcceptEncoding, 'offset': '2',
            'Stamp': self.__stamp__,
            'User-Agent': self.UserAgent, 'Connection': self.Connection, 'Content-Type': self.ContentJSON, 'ccsp-device-id': self.deviceId
        }
        data = {'targetSOClist': [{'plugType': 0, 'targetSOClevel': int(limit_fast)},
                                  {'plugType': 1, 'targetSOClevel': int(limit_slow)}]}
        response = requests.post(url, json=data, headers=headers, cookies=self.cookies, timeout=self.timeout)
        if response.status_code == 200:
            return True
        else:
            self.api_error('NOK setting charge limits. Error: ' + str(response.status_code) + response.text)
            return False


    def api_set_navigation(self, poi_info_list):
        if not self.check_control_token(): return False
        url = self.BaseURL + '/api/v2/spa/vehicles/' + self.vehicleId + '/location/routes'
        headers = {
            'Host': self.BaseHost, 'Accept': self.Accept, 'Authorization': self.controlToken,
            'ccsp-application-id': self.CcspApplicationId,
            'Accept-Language': self.AcceptLanguage, 'Accept-Encoding': self.AcceptEncoding, 'offset': '2',
            'Stamp': self.__stamp__,
            'User-Agent': self.UserAgent, 'Connection': self.Connection, 'Content-Type': self.ContentJSON, 'ccsp-device-id': self.deviceId
        }
        data = poi_info_list
        poi_info_list['deviceID'] = self.deviceId
        response = requests.post(url, json=poi_info_list, headers=headers, timeout=self.timeout)
        if response.status_code == 200:
            return True
        else:
            self.api_error('NOK setting navigation. Error: ' + str(response.status_code) + response.text)
            return False
        #TODO test what will happen if you send an array of 2 or more POI's, will it behave like a route-plan ?


    def api_get_userinfo(self):
        if not self.check_control_token(): return False
        # location
        url = self.BaseURL + '/api/v1/user/profile'
        headers = {
            'Host': self.BaseHost, 'Accept': self.Accept, 'Authorization': self.controlToken,
            'ccsp-application-id': self.CcspApplicationId,
            'Accept-Language': self.AcceptLanguage, 'Accept-Encoding': self.AcceptEncoding, 'offset': '2',
            'Stamp': self.__stamp__,
            'User-Agent': self.UserAgent, 'Connection': self.Connection, 'Content-Type': self.ContentJSON, 'ccsp-device-id': self.deviceId
        }
        response = requests.get(url, headers=headers, timeout=self.timeout)
        if response.status_code == 200:
            try:
                response = json.loads(response.text)
                return response
            except ValueError:
                self.api_error('NOK Getting user info: ' + response)
                return False
        else:
            self.api_error('NOK Getting user info. Error: ' + str(response.status_code) + response.text)
            return False


    def api_get_services(self):
        if not self.check_control_token(): return False
        # location
        url = self.BaseURL + '/api/v2/spa/vehicles/' + self.vehicleId + '/setting/service'
        headers = {
            'Host': self.BaseHost, 'Accept': self.Accept, 'Authorization': self.controlToken,
            'ccsp-application-id': self.CcspApplicationId,
            'Accept-Language': self.AcceptLanguage, 'Accept-Encoding': self.AcceptEncoding, 'offset': '2',
            'Stamp': self.__stamp__,
            'User-Agent': self.UserAgent, 'Connection': self.Connection, 'Content-Type': self.ContentJSON, 'ccsp-device-id': self.deviceId
        }
        response = requests.get(url, headers=headers, timeout=self.timeout)
        if response.status_code == 200:
            try:
                response = json.loads(response.text)
                return response['resMsg']['serviceCategorys']
                # returns array of booleans for each service in the list
                # 0= categoryname:1 = GIS
                # 1= categoryname:2 = Product and service improvements
                # 2= categoryname:3 = Alerts & security
                # 3= categoryname:4 = Vehicle Status (report, trips)
                # 4= categoryname:5 = Remote
            except ValueError:
                self.api_error('NOK Getting active services: ' + response)
                return False
        else:
            self.api_error('NOK Getting active services. Error: ' + str(response.status_code) + response.text)
            return False


    def api_set_activeservices(self, servicesonoff=[]):
        # servicesonoff is array of booleans for each service in the list
        # 0= categoryname:1 = GIS
        # 1= categoryname:2 = Product and service improvements
        # 2= categoryname:3 = Alerts & security
        # 3= categoryname:4 = Vehicle Status (report, trips)
        # 4= categoryname:5 = Remote
        if not self.check_control_token(): return False
        # location
        url = self.BaseURL + '/api/v2/spa/vehicles/' + self.vehicleId + '/setting/service'
        headers = {
            'Host': self.BaseHost, 'Accept': self.Accept, 'Authorization': self.controlToken,
            'ccsp-application-id': self.CcspApplicationId,
            'Accept-Language': self.AcceptLanguage, 'Accept-Encoding': self.AcceptEncoding, 'offset': '2',
            'Stamp': self.__stamp__,
            'User-Agent': self.UserAgent, 'Connection': self.Connection, 'Content-Type': self.ContentJSON, 'ccsp-device-id': self.deviceId
        }
        data=[]
        i = 0
        for service_on_off in servicesonoff:
            data['serviceCategorys'][i]['categoryName'] = i+1
            data['serviceCategorys'][i]['categoryStatus'] = service_on_off
        response = requests.post(url, data=data, headers=headers, timeout=self.timeout)
        if response.status_code == 200:
            try:
                response = json.loads(response.text)
                return response['resMsg']
            except ValueError:
                self.api_error('NOK Getting active services: ' + response)
                return False
        else:
            self.api_error('NOK Getting active services. Error: ' + str(response.status_code) + response.text)
            return False


    def api_get_monthlyreport(self, year, month):
        if not self.check_control_token(): return False
        # location
        url = self.BaseURL + '/api/v2/spa/vehicles/' + self.vehicleId + '/monthlyreport'
        headers = {
            'Host': self.BaseHost, 'Accept': self.Accept, 'Authorization': self.controlToken,
            'ccsp-application-id': self.CcspApplicationId,
            'Accept-Language': self.AcceptLanguage, 'Accept-Encoding': self.AcceptEncoding, 'offset': '2',
            'Stamp': self.__stamp__,
            'User-Agent': self.UserAgent, 'Connection': self.Connection, 'Content-Type': self.ContentJSON, 'ccsp-device-id': self.deviceId
        }
        data={'setRptMonth': "202006"}
        #data={'setRptMonth': str(year)+str(month)}
        response = requests.post(url, json=data, headers=headers, timeout=self.timeout)
        if response.status_code == 200:
            try:
                response = json.loads(response.text)
                return response['resMsg']['monthlyReport']
            except ValueError:
                self.api_error('NOK Getting montly report: ' + response)
                return False
        else:
            self.api_error('NOK Getting monthlyreport. Error: ' + str(response.status_code) + response.text)
            return False


    def api_get_monthlyreportlist(self):
        if not self.check_control_token(): return False
        # location
        url = self.BaseURL + '/api/v1/spa/vehicles/' + self.vehicleId + '/monthlyreportlist'
        headers = {
            'Host': self.BaseHost, 'Accept': self.Accept, 'Authorization': self.controlToken,
            'ccsp-application-id': self.CcspApplicationId,
            'Accept-Language': self.AcceptLanguage, 'Accept-Encoding': self.AcceptEncoding, 'offset': '2',
            'Stamp': self.__stamp__,
            'User-Agent': self.UserAgent, 'Connection': self.Connection, 'Content-Type': self.ContentJSON, 'ccsp-device-id': self.deviceId
        }
        response = requests.get(url, headers=headers, timeout=self.timeout)
        if response.status_code == 200:
            try:
                response = json.loads(response.text)
                return response['resMsg']['monthlyReport']
            except ValueError:
                self.api_error('NOK Getting montly reportlist: ' + response)
                return False
        else:
            self.api_error('NOK Getting monthlyreportlist. Error: ' + str(response.status_code) + response.text)
            return False

    # def api_error(self, message):
        # logger = logging.getLogger('root')
        # logger.error(message)
        # print(message)

    # TODO implement the other services
    '''
    api/v1/spa/vehicles/{carid}/monthlyreportlist —> doGetMVRInfoList    --> cant find it
    api/v1/spa/vehicles/{carid}/drvhistory —> doPostECOInfo 
    api/v1/spa/vehicles/{carid}/tripinfo —> doPostTripInfo --> 403 erorr unless i use V2 api
    api/v1/spa/vehicles/{carid}/profile —> doUpdateVehicleName

    api/v1/spa/vehicles/{carid}/location/park —>  doCarFinderLatestRequest

    api/v2/spa/vehicles/{carid}/control/engine —> doEngine
    api/v2/spa/vehicles/{carid}/control/horn —> doHorn
    api/v2/spa/vehicles/{carid}/control/light —> doLights
    '''
