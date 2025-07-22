# developer: varun pillai
# Description: Reverse engineered the code to authenticate to Tableau Server. 

from urllib.parse import urlparse, unquote
from bs4 import BeautifulSoup
import json
import re
from tableauscraper import dashboard
from tableauscraper import parameterControl
from tableauscraper import selectItem
from tableauscraper import utils
from tableauscraper import api
from tableauscraper import TableauScraper
from tableauscraper import api_tableau_server as api_ts
from tableauscraper import utils_tableau_server as utils_ts
from tableauscraper.TableauWorksheet import TableauWorksheet
from tableauscraper.TableauWorkbook import TableauWorkbook
import logging


class TableauServerScraper(TableauScraper):

    host: str = ""
    info = {}
    data = {}
    dashboard: str = ""
    tableauData = {}
    dataSegments = {}  # persistent data dictionary
    parameters = []  # persist parameter controls
    filters = {}  # persist filters per worksheet
    zones = {}  # persist zones
    logger = logging.getLogger("tableauScraper")
    delayMs = 500  # delay between actions (select/dropdown)
    lastActionTime = 0
    session = None
    verify = True

    def __init__(self, logLevel=logging.INFO, delayMs=500, verify=True):
        ch = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)
        self.logger.setLevel(logLevel)
        self.delayMs = delayMs
        self.tableauData = {}
        self.data = {}
        self.info = {}
        self.verify = verify
        super().__init__(logLevel, delayMs, verify)

    def loads(self, url, params={}):
        # url: "https://velocity.experian.com"
        # params["username"]: biquser
        # params["password"]: xxx
        # params["report"]: "views/checking/Sales"
        
        api.setSession(self)

        uri = urlparse(url)
        self.host = "{uri.scheme}://{uri.netloc}".format(uri=uri)

        # Generate a pubilc key that will be used to encrypt the user's password
        public_key = api_ts.generatePublicKey(self)
        pk = public_key["keyId"]
        
        # Encrypt the password used to login
        encryptedPassword = utils_ts.assymmetric_encrypt(params["password"],public_key)
        
        login_response = api_ts.vizportalLogin(self,params["username"], encryptedPassword, pk)

        if(login_response.status_code != 200):
            print("Login to Vizportal Failed!")
        else:
            report_url = f'{self.host}/{params["report"]}'
    
            r = api_ts.getTableauVizForSession(self, report_url)
            
            soup = BeautifulSoup(r, "html.parser")
            self.tableauData = json.loads(soup.find("textarea",{"id": "tsConfigContainer"}).text)

            if not params["filter"]:
                r = api_ts.getTableauData(self)
            else:
                r = api_ts.getTableauData(self, params["filter"])

            try:
                dataReg = re.search(r"\d+;({.*})\d+;({.*})", r, re.MULTILINE)
                self.info = json.loads(dataReg.group(1))
                self.data = json.loads(dataReg.group(2))

                if "presModelMap" in self.data["secondaryInfo"]:
                    presModelMap = self.data["secondaryInfo"]["presModelMap"]
                    self.dataSegments = presModelMap["dataDictionary"][
                        "presModelHolder"]["genDataDictionaryPresModel"]["dataSegments"]
                    self.parameters = utils.getParameterControlInput(
                        self.info)
                self.dashboard = self.info["sheetName"]
                self.filters = utils.getFiltersForAllWorksheet(
                    self.logger, self.data, self.info, rootDashboard=self.dashboard)
        
            except (AttributeError):
                raise TableauException(message=r)

    def getViewIds(self):
        return self.info["worldUpdate"]["applicationPresModel"]["workbookPresModel"]["dashboardPresModel"]["viewIds"]
    
    def getViewData(self, viewId):
        return api_ts.getViewData(self, viewId)
                                  
    def getWorkbook(self) -> TableauWorkbook:
        return dashboard.getWorksheets(self, self.data, self.info)

    def getWorksheet(self, worksheetName) -> TableauWorksheet:
        return dashboard.getWorksheet(self, self.data, self.info, worksheetName)

    def promptDashboard(self):
        return dashboard.get(self, self.data, self.info, self.logger)

    def promptParameters(self):
        return parameterControl.get(self, self.info, self.logger)

    def promptSelect(self):
        return selectItem.get(self, self.data, self.info, self.logger)
