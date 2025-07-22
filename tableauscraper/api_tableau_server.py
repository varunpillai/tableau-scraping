# developer: varun pillai
# Description: Reverse engineered the code to authenticate to Tableau Server. 

import json
from json.decoder import JSONDecodeError
import time
import requests
from tableauscraper import api
from tableauscraper import utils_tableau_server

def _encode_for_display(text):
    """
    Encodes strings so they can display as ASCII in a Windows terminal window.
    This function also encodes strings for processing by xml.etree.ElementTree functions.
    Returns an ASCII-encoded version of the text.
    Unicode characters are converted to ASCII placeholders (for example, "?").
    """
    return text.encode('ascii', errors="backslashreplace").decode('utf-8')

def generatePublicKey(scraper):
    dataUrl = f'{scraper.host}/vizportal/api/web/v1/generatePublicKey'
    payload = "{\"method\":\"generatePublicKey\",\"params\":{}}"

    r = scraper.session.post(
        dataUrl,
        data=payload,
        verify=scraper.verify
    )
    scraper.lastActionTime = time.time()
    response_text = json.loads(_encode_for_display(r.text))

    response_values = {"keyId":response_text["result"]["keyId"], "n":response_text["result"]["key"]["n"],"e":response_text["result"]["key"]["e"]}
    return response_values

def vizportalLogin(scraper, username, encryptedPassword, keyId):
    dataUrl = f'{scraper.host}/vizportal/api/web/v1/login'
    payload = "{\"method\":\"login\",\"params\":{\"username\":\"%s\", \"encryptedPassword\":\"%s\", \"keyId\":\"%s\"}}" % (username, encryptedPassword,keyId)
    r = scraper.session.post(
        dataUrl,
        data=payload,
        verify=scraper.verify
    )
    scraper.lastActionTime = time.time()
    return r

def getTableauVizForSession(scraper, url, params={}):
    if not params:
        params = {
            ":embed": "y",
            ":showVizHome": "no"
        }
    r = scraper.session.get(url, params=params,
                           verify=scraper.verify)
    return r.text

def getTableauData(scraper, filters=""):
    dataUrl = f'{scraper.host}{scraper.tableauData["vizql_root"]}/bootstrapSession/sessions/{scraper.tableauData["sessionid"]}'
    
    if filters:
        params = {
            "unknownParams": f"{filters}"
        }
    else:
        params = {}
        
    r = scraper.session.post(
        dataUrl,
        data={
            "sheet_id": scraper.tableauData["sheetId"],
            "showParams": json.dumps(params)
        },
        verify=scraper.verify
    )
    scraper.lastActionTime = time.time()
    return r.text

def getViewData(scraper, viewId):
    dataUrl = f'{scraper.host}/{scraper.tableauData["vizql_root"]}/vudcsv/sessions/{scraper.tableauData["sessionid"]}/views/{viewId}?summary=true'

    r = scraper.session.get(dataUrl,
                               verify=scraper.verify)
    scraper.lastActionTime = time.time()
    return r.text
