import time
import logging
import pickle
import json
import consolemenu
from generic_lib import georeverse, geolookup
from bluvo_main import BlueLink
from tools.stamps import postOffice

from params import *  # p_parameters are read

logging.basicConfig(format='%(asctime)s - %(levelname)-8s - %(filename)-18s - %(message)s', filename='bluvo_test.log',
                    level=logging.DEBUG)

menuoptions = ['0 exit', '1 log in', '2 initialise', '3 get stamp',
                "11 Lock", "12 Unlock", "13 Status", "14 Status formatted", "15 Status refresh", "16 location", "17 loop status",
               "18 Navigate to", '19 set Charge Limits', '20 get charge schedule', '21 get services', '22 poll car',  '23 get stamps', '24 odometer', '25 get park location',
               '26 get user info', '27 get monthly report', '28 get monthly report lists', '29 poll car without forced', '30 poll car with forced']
mymenu = consolemenu.SelectionMenu(menuoptions)
# heartbeatinterval, initsuccess = initialise(p_email, p_password, p_pin, p_vin, p_abrp_token, p_abrp_carmodel, p_WeatherApiKey,
                         # p_WeatherProvider, p_homelocation, p_forcepollinterval, p_charginginterval,
                         # p_heartbeatinterval)
logging.info("starting test run")
bluelink = None
if True:
#if bluelink.initSuccess:
    #stampie = postOffice("hyundai", False)
    while True:
        for i in menuoptions:
            print(i) 
        #try:
        x = int(input("Please Select:"))
        logging.debug("menu option: "+str(x))
        if x == 0: 
             logging.info("stopping test run")
             exit()
        if x == 1:
            bluelink = BlueLink(p_email, p_password, p_pin, p_vin, p_abrp_carmodel, p_abrp_token, p_WeatherApiKey, p_WeatherProvider, p_homelocation)
        if x == 2:
            bluelink.initialise(p_forcepollinterval, p_charginginterval)
        if x == 3:  
            bluelink.vehicle.stamp = bluelink.stampProvider.getStamp()
            print(bluelink.vehicle.stamp)
        if x == 11: bluelink.vehicle.api_set_lock('on')
        if x == 12: bluelink.vehicle.api_set_lock('off')
        if x == 13: print(bluelink.vehicle.api_get_status(False))
        if x == 14: 
            status_record = bluelink.vehicle.api_get_status(False)
            print(json.dumps(status_record, sort_keys = True, indent=4))
        if x == 15: print(json.dumps(bluelink.vehicle.api_get_status(True), sort_keys = True, indent=4))
        if x == 16:
            locatie = bluelink.vehicle.api_get_location()
            if locatie:
                locatie = locatie['gpsDetail']['coord']
                print(georeverse(locatie['lat'], locatie['lon']))
        if x == 17:
            while True:
                # read semaphore flag
                try:
                    with open('semaphore.pkl', 'rb') as f:
                        manualForcePoll = pickle.load(f)
                except:
                    manualForcePoll = False
                print(manualForcePoll)
                updated, parsedStatus, afstand, googlelocation = bluelink.pollcar(manualForcePoll)
                # clear semaphore flag
                manualForcePoll = False
                with open('semaphore.pkl', 'wb') as f:
                    pickle.dump(manualForcePoll, f)

                if updated:
                    print('afstand van huis, rijrichting, snelheid en km-stand: ', afstand, ' / ',
                          parsedStatus['heading'], '/', parsedStatus['speed'], '/', parsedStatus['odometer'])
                    print(googlelocation)
                    print("range ", parsedStatus['range'], "soc: ", parsedStatus['chargeHV'])
                    if parsedStatus['charging']: print("Laden")
                    if parsedStatus['trunkopen']: print("kofferbak open")
                    if not (parsedStatus['locked']): print("deuren van slot")
                    if parsedStatus['dooropenFL']: print("bestuurdersportier open")
                    print("soc12v ", parsedStatus['charge12V'], "status 12V", parsedStatus['status12V'])
                    print("=============")
                time.sleep(bluelink.heartbeatinterval)
        if x == 18: print(bluelink.vehicle.api_set_navigation(geolookup(input("Press Enter address to navigate to..."))))
        if x == 19:
            invoer = input("Enter maximum for fast and slow charging (space or comma or semicolon or colon seperated)")
            for delim in ',;:': invoer = invoer.replace(delim, ' ')
            print(bluelink.vehicle.api_set_chargelimits(invoer.split()[0], invoer.split()[1]))

        if x == 20: print(json.dumps(bluelink.vehicle.api_get_chargeschedule(),indent=4))
        if x == 21: print(json.dumps(bluelink.vehicle.api_get_services(),indent=4))
        if x == 22: print(str(bluelink.pollcar(True)))
        if x == 23:
            print( "feature removed")
        if x == 24: print(bluelink.vehicle.api_get_odometer())
        if x == 25: print(json.dumps(bluelink.vehicle.api_get_parklocation(), indent=4))
        if x == 26: print(json.dumps(bluelink.vehicle.api_get_userinfo(), indent=4))
        if x == 27: print(json.dumps(bluelink.vehicle.api_get_monthlyreport(2021,5), indent=4))
        if x == 28: print(json.dumps(bluelink.vehicle.api_get_monthlyreportlist(), indent=4))
        if x == 29: print(json.dumps(bluelink.pollcar(False), indent=4))
        if x == 30: print(json.dumps(bluelink.pollcar(True), indent=4))
        input("Press Enter to continue...")
        # except (ValueError) as err:
            # print("error in menu keuze")
else:
    logging.error("initialisation failed")

