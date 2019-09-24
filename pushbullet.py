#!/usr/bin/env python3
import logging, requests, argparse, sys, json
from logging import handlers
from logging.handlers import RotatingFileHandler
from requests.auth import HTTPDigestAuth

# rest of logging caught by calling script
log = logging.getLogger("")

# stdout handler
logformat = logging.Formatter("%(levelname)s %(asctime)s (%(name)s) %(message)s")
ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(logformat)
log.addHandler(ch)

log.info("testing")

# read config file
try:
    with open('/home/pi/piscripts/sort.config.json') as json_data_file:
        data = json.load(json_data_file)
except FileNotFoundError as e:
    log.debug("Config file not found, try windows path")
    try:
        with open('sort.config.json') as json_data_file:
            data = json.load(json_data_file)
    except FileNotFoundError as e:
        msg = "Sort config file not found, aborting (from pushbullet.py)"
        log.error(msg)
        sys.exit (0)

def send(msg, notify = True):
    log.debug("pushbullet message: " + str(msg))
    if not notify:
        log.info("** quiet mode, no messages **")
    # pushbullet api token stuff
    pbtoken = data["advanced"]["notifications"]["pbtoken"]
    pburl = data["advanced"]["notifications"]["pburl"]
    
    # set some session headers
    session = requests.Session() # for pushbullet api calls
    session.headers.update({"Accept": "application/json", "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
    session.headers.update({"Access-Token": pbtoken})
    
    pbdata = '{"type": "note", "title":"' + msg[0] + '", "body":"' + msg[1] + '"}'
    
    # send message
    if notify:
        try:
            request = session.post(pburl, data=pbdata)
            log.debug("pushbullet response = " + str(request))
            if request.status_code == 400:
                log.error("error code 400")
                pbdata = '{"type": "note", "title":"Sort Error", "body":"script hit an error in sending"}'
                request = session.post(pburl, data=pbdata)
        except Exception as e:
            log.error("error sending message: " + str(msg) + " - error:" + str(e))