import random
import logging
import requests
import datetime

class postOffice():
    def __init__(self, carbrand, appId = "", local=False):
        self.__use_local__ = local
        self.expiry_date = datetime.datetime.now()
        self.stampList = []
        self.carbrand = carbrand
        self.__stampValid = False
        if appId == "":
            self.__appId = appId
        else:
            self.__appId = "-" + appId + ".v2"
        self.log_info = { 'class': 'postOffice'}
        self.file_expiry_days = 6

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
        self.expiry_date = datetime.datetime.now() + datetime.timedelta(days=self.file_expiry_days)
        return True

    def getStampListFromUrl(self, stampsFile = "https://raw.githubusercontent.com/neoPix/bluelinky-stamps/master/"):
        url = stampsFile + self.carbrand + self.__appId + ".json"
        logging.info("PostOffice: getStampFromUrl: reading from URL: " + url)
        body = requests.get(url)
        logging.debug("PostOffice: received response: {0}".format(body))
        stampStruct = body.json()
        stampList = stampStruct["stamps"]
        stampsGenerated = stampStruct["generated"][:-1] #date time of stamps generated, stripping the last character
        frequency = stampStruct["frequency"] #interval between stamps in msec
        timeDelta = datetime.datetime.utcnow() - datetime.datetime.fromisoformat(stampsGenerated)
        offset = int(timeDelta.total_seconds()*1000 / int(frequency))
        self.stampList = stampList[offset:]
        logging.debug("PostOffice: received stamps list length: {0} generated at {1}".format(len(self.stampList),stampsGenerated))
        logging.debug("offset {0}, datetime.fromisoformat(stampsGenerated) = {1}, frequency = {2}".format(offset,datetime.datetime.fromisoformat(stampsGenerated),frequency))
        self.expiry_date = datetime.datetime.now() + datetime.timedelta(days=self.file_expiry_days)
        return True
    
    def getStamp(self):
        #get a stamp from the list and remove it
        self.checkStampValid()
        logging.info('PostOffice: handig out a new stamp')
        #return self.stampList.pop(random.randrange(len(self.stampList))).rstrip("\n")
        return self.stampList.pop(0).rstrip("\n")
        
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