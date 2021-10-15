from datetime import datetime
from bluvo_lib import vehicleInteraction
from generic_lib import distance, hex2temp
import logging
import random
from abrp import ABRP
# todo make object oriented

class BlueLink:
    pollcounter = 0
    oldstatustime = ""
    oldpolltime = ""
    forcepollinterval = 0
    charginginterval = 0
    def __init__(self, email, password, pin, vin, abrp_carmodel, abrp_token, weather_api_key, weather_provider, homelocation):
        self.email = email
        self.password = password
        self.pin = pin
        self.vin = vin
        self.initSuccess = False
        loc = homelocation.split(";")
        self.homelat = float(loc[0])
        self.homelon = float(loc[1])
        self.abrp_carmodel = abrp_carmodel
        self.car_brand = (self.abrp_carmodel.split(":", 1)[0])
        self.abrp = ABRP(self.abrp_carmodel, abrp_token, weather_api_key, weather_provider)
        self.vehicle = vehicleInteraction(self.car_brand)
        return
    
    def process_data(self, carstatus, location, odometer):
        # this procedure does a few things
        # generate pretty data == parsed status
        # calculate distance from home
        # create a Google Maps link for location
        # send data to ABRP
        afstand = 0
        googlelocation = ""
        parsedstatus = {}
        #try:
        parsedstatus = {
            'hoodopen': carstatus['hoodOpen'],
            'trunkopen': carstatus['trunkOpen'],
            'locked': carstatus['doorLock'],
            'dooropenFL': carstatus['doorOpen']['frontLeft'],
            'dooropenFR': carstatus['doorOpen']['frontRight'],
            'dooropenRL': carstatus['doorOpen']['backLeft'],
            'dooropenRR': carstatus['doorOpen']['backRight'],
            'dooropenANY': (carstatus['doorOpen']['frontLeft'] or carstatus['doorOpen']['backLeft'] or carstatus['doorOpen']['backRight'] or carstatus['doorOpen']['frontRight']),
            'tirewarningFL': carstatus['tirePressureLamp']['tirePressureLampFL'],
            'tirewarningFR': carstatus['tirePressureLamp']['tirePressureLampFR'],
            'tirewarningRL': carstatus['tirePressureLamp']['tirePressureLampRL'],
            'tirewarningRR': carstatus['tirePressureLamp']['tirePressureLampRR'],
            'tirewarningall': carstatus['tirePressureLamp']['tirePressureLampAll'],
            'climateactive': carstatus['airCtrlOn'],
            'steerwheelheat': carstatus['steerWheelHeat'],
            'rearwindowheat': carstatus['sideBackWindowHeat'],
            'temperature': hex2temp(carstatus['airTemp']['value']),
            'defrost': carstatus['defrost'],
            'engine': carstatus['engine'],
            'acc': carstatus['acc'],
            'range': carstatus['evStatus']['drvDistance'][0]['rangeByFuel']['totalAvailableRange']['value'],
            'charge12V': carstatus['battery']['batSoc'],
            'status12V': carstatus['battery']['batState'],
            'charging': carstatus['evStatus']['batteryCharge'],
            'chargeHV': carstatus['evStatus']['batteryStatus'],
            'pluggedin': carstatus['evStatus']['batteryPlugin'],
            'heading': location['head'],
            'speed': location['speed']['value'],
            'loclat': location['coord']['lat'],
            'loclon': location['coord']['lon'],
            'odometer': odometer,
            'time': carstatus['time'],
            'chargingTime': carstatus['evStatus']['remainTime2']['atc'] ['value']
        }
        afstand = round(distance(parsedstatus['loclat'], parsedstatus['loclon'], float(self.homelat), float(self.homelon)), 1)
        googlelocation = 'href="http://www.google.com/maps/search/?api=1&query=' + str(parsedstatus['loclat']) + ',' + str(
            parsedstatus['loclon']) + '">'
        self.abrp.send_abr_ptelemetry(parsedstatus['chargeHV'], parsedstatus['speed'], parsedstatus['loclat'], parsedstatus['loclon'], parsedstatus['charging'])
        # except:
            # logging.error("something went wrong in process data procedure")
        return parsedstatus, afstand, googlelocation


    def initialise(self, p_forcepollinterval, p_charginginterval):
        # heartbeatinterval
        # p_parameters are fed into global variables
        logging.debug("into Initialise")
        if p_forcepollinterval == "":
            self.forcepollinterval = float(60*60)
        else:
            self.forcepollinterval = float(p_forcepollinterval)*60
        if p_charginginterval == "":
            self.charginginterval = float(self.forcepollinterval) / 4
        else:
            self.charginginterval = float(p_charginginterval) * 60
        logging.debug("forcedpoll: %s, charging: %s", self.forcepollinterval, self.charginginterval)
        self.oldstatustime = ""
        self.oldpolltime = ""
        self.pollcounter = 7
        logging.debug("trying to login")
        self.initSuccess = self.vehicle.login_legacy(self.email, self.password, self.pin, self.vin)
        logging.debug("login result: " + str(self.initSuccess))
        return 


    def pollcar(self, manualForcePoll):
        # get statusses from car; either cache or refreshed
        # return as [updated,[carstatus],[odometer],[location]]
        # return False if it fails (behaves as if info did not change)
        # reset pollcounter at start of day
        break_point = "start poll procedure"  # breakpoint
        carstatus = "empty car status"
        if self.oldpolltime == "": 
            self.pollcounter = 0
        else:
            if self.oldpolltime.date() != datetime.now().date(): 
                self.pollcounter = 0
        parsed_status = {}
        updated = False
        afstand = 0
        googlelocation = ''
        #try:
        self.pollcounter += 1
        carstatus = self.vehicle.api_get_status(False)
        break_point = "got status"
        if carstatus is not False:
            logging.debug('carstatus in cache %s', carstatus)
            odometer = carstatus['vehicleStatusInfo']['odometer']['value']
            location = carstatus['vehicleStatusInfo']['vehicleLocation']
            carstatus = carstatus['vehicleStatusInfo']['vehicleStatus']
            # use the vehicle status to determine stuff and shorten script
            if self.oldstatustime != carstatus['time']:
                logging.debug('new timestamp of cache data (was %s now %s), about to process it', self.oldstatustime, carstatus['time'])
                parsed_status, afstand, googlelocation = self.process_data(carstatus, location, odometer)
                self.oldstatustime = carstatus['time']
                updated = True
            else:
                logging.debug("self.oldstatustime == carstatus['time']")
            try: sleepmodecheck = carstatus['sleepModeCheck']
            except KeyError: sleepmodecheck = False  # sleep mode check is not there...
            # at minimum every interval minutes a true poll
            forcedpolltimer = False
            if self.oldpolltime == '': 
                forcedpolltimer = True  # first run
            else:
                if (float((datetime.now() - self.oldpolltime).total_seconds()) >= random.uniform(0.75, 1.5)*self.forcepollinterval): forcedpolltimer = True
                else:
                    if carstatus['evStatus']['batteryCharge']:
                        if (float((datetime.now() - self.oldpolltime).total_seconds()) >= random.uniform(0.75, 1.5)*self.charginginterval): forcedpolltimer = True

            break_point = "Before checking refresh conditions"
            if sleepmodecheck or forcedpolltimer or manualForcePoll or carstatus['engine']:
                strings = ["sleepmodecheck", "forcedpolltimer", "manualForcePoll", "engine", 'charging']
                conditions = [sleepmodecheck, forcedpolltimer, manualForcePoll, carstatus['engine'], carstatus['evStatus']['batteryCharge']]
                truecond = ''
                for i in range(len(strings)):
                    if conditions[i]: truecond += (" " + strings[i])
                logging.info("these conditions for a reload were true:%s", truecond)
                self.pollcounter += 1
                carstatus = self.vehicle.api_get_status(True)

                if carstatus is not False:
                    logging.debug('information after refresh engine: %s; trunk: %s; doorunlock %s; charging %s',
                                  carstatus['engine'], carstatus['trunkOpen'], not(carstatus['doorLock']), carstatus['evStatus']['batteryCharge'])
                    self.pollcounter += 1
                    carstatus = self.vehicle.api_get_status(False)

                    if carstatus is not False:

                        freshodometer = carstatus['vehicleStatusInfo']['odometer']['value']
                        carstatus = carstatus['vehicleStatusInfo']['vehicleStatus']
                        logging.debug('information in cache ==> engine: %s; trunk: %s; doorunlock %s; charging %s; odometer %s',
                                      carstatus['engine'], carstatus['trunkOpen'], not(carstatus['doorLock']), carstatus['evStatus']['batteryCharge'], freshodometer)
                        # when car is moging (engine is running or odometer changed) ask for a location update
                        logging.debug("odometer before refresh %s and after %s", odometer, freshodometer)
                        if carstatus['engine'] or (freshodometer != odometer):
                            self.pollcounter += 1
                            freshlocation = api_get_location()

                            if freshlocation is not False:
                                freshlocation = freshlocation['gpsDetail']
                                logging.debug('location before refresh %s and after %s', location['coord'], freshlocation['coord'])
                                location = freshlocation
                        odometer = freshodometer
                        self.oldpolltime = datetime.now()
                        self.oldstatustime = carstatus['time']
                        updated = True
                        # logging.debug("entering worker with location %s and status %s", freshlocation, carstatus)
                        parsed_status, afstand, googlelocation = self.process_data(carstatus, location, odometer)
        else:
            logging.debug("carstatus is False")
        # except:
            # self.oldpolltime = datetime.now()
            # logging.error('error in poll procedure, breakpoint: %s', break_point)
            # logging.error('carstatus: %s', carstatus)
        logging.debug('pollcount: %s', self.pollcounter)
        return updated, parsed_status, afstand, googlelocation


    def setcharge(self, command):
        return api_set_charge(command)


    def lockdoors(self, command):
        return api_set_lock(command)


    def setairco(self, action, temp):
        return api_set_hvac(action, temp, False, False)
