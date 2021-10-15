import random
import logging
import requests
import datetime

class postOffice():
    def __init__(self, carbrand, local=False):
        self.use_local = local
        self.expiry_date = datetime.datetime.now()
        self.stampList = []
        self.carbrand = carbrand
        
    def getStampListFromLocal(self):
        filename = self.carbrand+'list.txt'
        logging.info('CreateStamp: reading stamp from file: ' + filename)
        with open(self.carbrand+'list.txt') as f:
            self.list = f.readlines()
        self.expiry_date = datetime.datetime.now() + datetime.timedelta(days=7)
        #return random.choice(lines).rstrip("\n")
        return True

    def getStampListFromUrl(self, stampsFile = "https://raw.githubusercontent.com/neoPix/bluelinky-stamps/master/"):
        # if (stampsFile.startsWith('file://')) :
            # const [,path] = stampsFile.split('file://');
            # const content = await promisify(readFile)(path);
            # return JSON.parse(content.toString('utf-8'));
        # }
        url = stampsFile + self.carbrand + ".json"
        logging.info("getStampFromUrl: reading from URL: " + url)
        body = requests.get(url)
        logging.debug("length of received stamps list: {0}".format(len(body.json())))
        self.stampList = body.json()
        self.expiry_date = datetime.datetime.now() + datetime.timedelta(days=7)
        return True
        #return random.choice(body.json()).rstrip("\n");
    
    def getStamp(self):
        #get a stamp from the list and remove it
        self.checkStampValid()
        return self.stampList.pop(random.randrange(len(self.stampList)))
        
    def checkStampValid(self):
        logging.info("we have " + str(len(self.stampList)) + " stamps that expire at " + self.expiry_date.strftime("%Y-%m-%d %H:%M:%S"))
        if len(self.stampList)<=0 or self.expiry_date <= datetime.datetime.now():
            #need to get new stamp list
            if self.use_local:
                self.getStampListFromLocal()
            else:
                self.getStampListFromUrl()
            logging.debug("we have " + str(len(self.stampList)) + " stamps that expire at " + self.expiry_date.strftime("%Y-%m-%d %H:%M:%S"))
        return
