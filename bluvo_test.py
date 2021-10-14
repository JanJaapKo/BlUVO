import time
import logging
import pickle
import json
import consolemenu
from generic_lib import georeverse, geolookup
from bluvo_main import BlueLink

from params import *  # p_parameters are read

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', filename='bluvo_test.log',
                    level=logging.DEBUG)

menuoptions = ["0 Lock", "1 Unlock", "2 Status", "3 Status formatted", "4 Status refresh", "5 location", "6 loop status",
               "7 Navigate to", '8 set Charge Limits', '9 get charge schedule', '10 get services', '11 poll car', '12 exit']
mymenu = consolemenu.SelectionMenu(menuoptions)
# heartbeatinterval, initsuccess = initialise(p_email, p_password, p_pin, p_vin, p_abrp_token, p_abrp_carmodel, p_WeatherApiKey,
                         # p_WeatherProvider, p_homelocation, p_forcepollinterval, p_charginginterval,
                         # p_heartbeatinterval)

bluelink = BlueLink(p_email, p_password, p_pin, p_vin, p_abrp_carmodel, p_abrp_token, p_WeatherApiKey, p_WeatherProvider, p_homelocation)
bluelink.initialise(p_forcepollinterval, p_charginginterval)

if bluelink.initSuccess:
    while True:
        for i in menuoptions:
            print(i) 
        try:
            x = int(input("Please Select:"))
            print(x)
            if x == 0: bluelink.vehicle.api_set_lock('on')
            if x == 1: bluelink.vehicle.api_set_lock('off')
            if x == 2: print(bluelink.vehicle.api_get_status(False))
            if x == 3: print(bluelink.vehicle.api_get_status(False, False))
            if x == 4: print(bluelink.vehicle.api_get_status(True))
            if x == 5:
                locatie = bluelink.vehicle.api_get_location()
                if locatie:
                    locatie = locatie['gpsDetail']['coord']
                    print(georeverse(locatie['lat'], locatie['lon']))
            if x == 6:
                while True:
                    # read semaphore flag
                    try:
                        with open('semaphore.pkl', 'rb') as f:
                            manualForcePoll = pickle.load(f)
                    except:
                        manualForcePoll = False
                    print(manualForcePoll)
                    updated, parsedStatus, afstand, googlelocation = bluelink.vehicle.pollcar(manualForcePoll)
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
                    time.sleep(heartbeatinterval)
            if x == 7: print(bluelink.vehicle.api_set_navigation(geolookup(input("Press Enter address to navigate to..."))))
            if x == 8:
                invoer = input("Enter maximum for fast and slow charging (space or comma or semicolon or colon seperated)")
                for delim in ',;:': invoer = invoer.replace(delim, ' ')
                print(bluelink.vehicle.api_set_chargelimits(invoer.split()[0], invoer.split()[1]))

            if x == 9: print(json.dumps(bluelink.vehicle.api_get_chargeschedule(),indent=4))
            if x == 10: print(bluelink.vehicle.api_get_services())
            if x == 11: bluelink.pollcar(True)
            if x == 12: exit()
            input("Press Enter to continue...")
        except (ValueError) as err:
            print("error in menu keuze")
else:
    logging.error("initialisation failed")

