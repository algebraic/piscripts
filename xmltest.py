#!/usr/bin/env python3
import argparse
import logging
import sys
import xml.etree.ElementTree as ET
from logging import handlers
from logging.handlers import RotatingFileHandler
from subprocess import call

import requests

# set logging
log = logging.getLogger("")
log.setLevel("DEBUG")
# LOG_FILE = "/var/log/xmltest.log"
LOG_FILE = "xmltest.log"
logformat = logging.Formatter("%(levelname)s %(asctime)s (%(name)s) %(message)s")
##DEBUG (debug stuff & extra stuff from urllib3.connectionpool)
##INFO (regular sort operations)
##WARNING (can't find show, episode, movie...)
##ERROR (just errors)
##CRITICAL (problems with an api or filename confusion)

# stdout handler
ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(logformat)
log.addHandler(ch)
# file handler
fh = handlers.RotatingFileHandler(LOG_FILE, maxBytes=(1048576*5), backupCount=7)
fh.setFormatter(logformat)
log.addHandler(fh)

log.debug("starting xmltest.py")

def loadRSS(): 
    # url of rss feed 
    url = 'http://showrss.info/user/4242.rss'

    # creating HTTP response object from given url 
    resp = requests.get(url) 

    # saving the xml file 
    with open('showrss.xml', 'wb') as f: 
        f.write(resp.content) 


def parseXML(xmlfile): 
    # create element tree object 
    tree = ET.parse(xmlfile) 
  
    # get root element 
    root = tree.getroot() 
  
    print("####################")

    # create empty list for news items 
    shows = [] 
  
    # iterate news items 
    for item in root.findall('./channel/item'): 
        # iterate child elements of item 
        for child in item: 
            if child.tag == "title": 
                print(child.tag)
                print(child.text)

    # return news items list 
    return shows 

def main(): 
    # load rss from web to update existing xml file 
    loadRSS() 
  
    # parse xml file 
    shows = parseXML('showrss.xml') 
  
    # store news items in a csv file 
    log.debug("test load completed?")
      
      
if __name__ == "__main__": 
    # calling main function 
    main() 