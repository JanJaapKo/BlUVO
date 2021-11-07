import random
import logging
import requests
import datetime

class postOffice():
    def __init__(self, carbrand, local=False):
        self.__use_local__ = local
        self.expiry_date = datetime.datetime.now()
        self.stampList = []
        self.carbrand = carbrand
        self.__stampValid = False
        self.log_info = { 'class': 'postOffice'}

    @property
    def use_local(self):
        return self.__use_local__
        
    @use_local.setter
    def use_local(self, use):
        self.__use_local__ = use
        
    def getStampListFromLocal(self):
        filename = self.carbrand+'list.txt'
        logging.info('PostOffice: CreateStamp: reading stamp from file: ' + filename)
        with open(self.carbrand+'list.txt') as f:
            self.stampList = f.readlines()
        self.expiry_date = datetime.datetime.now() + datetime.timedelta(days=7)
        #return random.choice(lines).rstrip("\n")
        return True

    def getStampListFromUrl(self, stampsFile = "https://raw.githubusercontent.com/neoPix/bluelinky-stamps/master/"):
        url = stampsFile + self.carbrand + ".json"
        logging.info("PostOffice: getStampFromUrl: reading from URL: " + url)
        body = requests.get(url)
        logging.debug("PostOffice: length of received stamps list: {0}".format(len(body.json())))
        self.stampList = body.json()
        self.expiry_date = datetime.datetime.now() + datetime.timedelta(days=7)
        return True
        #return random.choice(body.json()).rstrip("\n");
    
    def getStamp(self):
        #get a stamp from the list and remove it
        self.checkStampValid()
        logging.info('PostOffice: handig out a new stamp')
        return self.stampList.pop(random.randrange(len(self.stampList))).rstrip("\n")
        
    def checkStampValid(self):
        logging.info("we have " + str(len(self.stampList)) + " stamps that expire at " + self.expiry_date.strftime("%Y-%m-%d %H:%M:%S"))
        if len(self.stampList)<=0 or self.expiry_date <= datetime.datetime.now():
            #need to get new stamp list
            if self.__use_local__:
                self.getStampListFromLocal()
            else:
                self.getStampListFromUrl()
            logging.debug("PostOffice: we have " + str(len(self.stampList)) + " stamps that expire at " + self.expiry_date.strftime("%Y-%m-%d %H:%M:%S"))
            self.__stampValid = True
        return

    @property
    def stampValid(self):
        return self.__stampValid
    
    @stampValid.setter
    def stampValid(self, state):
        logging.debug('PostOffice: setting stamp validity to ' + str(state))
        self.__stampValid = state