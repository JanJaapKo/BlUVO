import random
import logging
import requests
import datetime

class postOffice():
    def __init__(self, carbrand, appId = "", local=False):
        self.__use_local__ = local
        self.file_expiry_date = datetime.datetime.now()
        self.stamp_expiry_DT = datetime.datetime.now()
        self.stampList = []
        self.carbrand = carbrand
        self.__stampValid = False
        self.__stampFileValid = False
        self.__activeStamp = 0
        self.__frequency = 1
        self.__stampsGenerated = datetime.datetime.now()
        if appId == "":
            self.__appId = appId
        else:
            self.__appId = "-" + appId + ".v2"
        self.log_info = { 'class': 'postOffice'}
        self.file_expiry_days = 6
        self.__stamp_expiry_time = datetime.timedelta(seconds=5*60) #time the stamps are valid in seconds

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
        self.file_expiry_date = datetime.datetime.now() + datetime.timedelta(days=self.file_expiry_days)
        return True

    def getOffset(self):
        #calculate the offset from the start of the list to find the stamp that should be valid now
        timeDelta = datetime.datetime.utcnow() - self.__stampsGenerated #stamps generated is in UTC
        self.__activeStamp = int(timeDelta.total_seconds()*1000 / int(self.__frequency))
        return self.__activeStamp

    def getStampListFromUrl(self, stampsFile = "https://raw.githubusercontent.com/neoPix/bluelinky-stamps/master/"):
        url = stampsFile + self.carbrand + self.__appId + ".json"
        logging.info("PostOffice: getStampFromUrl: reading from URL: " + url)
        body = requests.get(url)
        logging.debug("PostOffice: received response: {0}".format(body))
        stampStruct = body.json()
        self.stampList = stampStruct["stamps"]
        stampsGenerated = stampStruct["generated"][:-1] #date time of stamps generated, stripping the UTC z
        self.__frequency = stampStruct["frequency"] #interval between stamps in msec
        self.__stampsGenerated = datetime.datetime.fromisoformat(stampsGenerated)
        self.getOffset()
        logging.debug("PostOffice: received stamps list length: {0} generated at {1}".format(len(self.stampList),self.__stampsGenerated))
        logging.debug("offset {0}, datetime.fromisoformat(stampsGenerated) = {1}, frequency = {2}".format(self.__activeStamp, self.__stampsGenerated, self.__frequency))
        self.file_expiry_date = self.__stampsGenerated + datetime.timedelta(seconds=(self.__frequency/1000*len(self.stampList)))
        return True
    
    def getStamp(self):
        #get a stamp from the list
        self.checkStampValid()
        logging.info('PostOffice: handig out a new stamp, number ' + str(self.__activeStamp) + ' from the list')
        self.stamp_expiry_DT = datetime.datetime.now() + self.__stamp_expiry_time
        return self.stampList[self.__activeStamp].rstrip("\n")
        
    def checkStampValid(self):
        #self.getOffset()
        logging.info("PostOffice: we have " + str(len(self.stampList)) + " stamps, using " + str(self.__activeStamp) + " the list expires at " + self.file_expiry_date.strftime("%Y-%m-%d %H:%M:%S"))
        #if len(self.stampList)<=0 or self.file_expiry_date <= datetime.datetime.now() or self.__activeStamp>=len(self.stampList):
        if self.stampFileValid == False:
            #need to get new stamp list
            if self.__use_local__:
                self.getStampListFromLocal()
            else:
                self.getStampListFromUrl()
            logging.debug("PostOffice: we have " + str(len(self.stampList)) + " stamps, using " + str(self.__activeStamp) + " the list expires at " + self.file_expiry_date.strftime("%Y-%m-%d %H:%M:%S"))
            self.__stampValid = True
        if self.stamp_expiry_DT < datetime.datetime.now():
            self.__stampValid = False

        return

    @property
    def stampValid(self):
        return self.__stampValid
    
    @stampValid.setter
    def stampValid(self, state):
        logging.debug('PostOffice: setting stamp validity to ' + str(state))
        self.__stampValid = state
        
    @property
    def stampFileValid(self):
        self.getOffset()
        self.__stampFileValid = ((datetime.datetime.now() < self.file_expiry_date) and self.__activeStamp<=len(self.stampList) and len(self.stampList)>0)
        return self.__stampFileValid
