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

menuoptions = ['0 exit',"1 Lock", "2 Unlock", "3 Status", "4 Status formatted", "5 Status refresh", "6 location", "7 loop status",
               "8 Navigate to", '9 set Charge Limits', '10 get charge schedule', '11 get services', '12 poll car',  '13 get stamps', '14 odometer', '15 get park location',
               '16 get user info', '17 get monthly report', '18 get monthly report lists']
mymenu = consolemenu.SelectionMenu(menuoptions)
# heartbeatinterval, initsuccess = initialise(p_email, p_password, p_pin, p_vin, p_abrp_token, p_abrp_carmodel, p_WeatherApiKey,
                         # p_WeatherProvider, p_homelocation, p_forcepollinterval, p_charginginterval,
                         # p_heartbeatinterval)

bluelink = BlueLink(p_email, p_password, p_pin, p_vin, p_abrp_carmodel, p_abrp_token, p_WeatherApiKey, p_WeatherProvider, p_homelocation)
bluelink.initialise(p_forcepollinterval, p_charginginterval)

if bluelink.initSuccess:
    #stampie = postOffice("hyundai", False)
    while True:
        for i in menuoptions:
            print(i) 
        #try:
        x = int(input("Please Select:"))
        print(x)
        if x == 0: exit()
        if x == 1: bluelink.vehicle.api_set_lock('on')
        if x == 2: bluelink.vehicle.api_set_lock('off')
        if x == 3: print(bluelink.vehicle.api_get_status(False))
        if x == 4: 
            status_record = bluelink.vehicle.api_get_status(False)
            print(json.dumps(status_record, sort_keys = True, indent=4))
        if x == 5: print(json.dumps(bluelink.vehicle.api_get_status(True), sort_keys = True, indent=4))
        if x == 6:
            locatie = bluelink.vehicle.api_get_location()
            if locatie:
                locatie = locatie['gpsDetail']['coord']
                print(georeverse(locatie['lat'], locatie['lon']))
        if x == 7:
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
        if x == 8: print(bluelink.vehicle.api_set_navigation(geolookup(input("Press Enter address to navigate to..."))))
        if x == 9:
            invoer = input("Enter maximum for fast and slow charging (space or comma or semicolon or colon seperated)")
            for delim in ',;:': invoer = invoer.replace(delim, ' ')
            print(bluelink.vehicle.api_set_chargelimits(invoer.split()[0], invoer.split()[1]))

        if x == 10: print(json.dumps(bluelink.vehicle.api_get_chargeschedule(),indent=4))
        if x == 11: print(bluelink.vehicle.api_get_services())
        if x == 12: print(str(bluelink.pollcar(True)))
        if x == 13:
            print( "feature removed")
        if x == 14: print(bluelink.vehicle.api_get_odometer())
        if x == 15: print(json.dumps(bluelink.vehicle.api_get_parklocation(), indent=4))
        if x == 16: print(json.dumps(bluelink.vehicle.api_get_userinfo(), indent=4))
        if x == 17: print(json.dumps(bluelink.vehicle.api_get_monthlyreport(2021,5), indent=4))
        if x == 18: print(json.dumps(bluelink.vehicle.api_get_monthlyreportlist(), indent=4))
        input("Press Enter to continue...")
        # except (ValueError) as err:
            # print("error in menu keuze")
else:
    logging.error("initialisation failed")

