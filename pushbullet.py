#!/usr/bin/env python3
import logging, requests, argparse
from logging import handlers
from logging.handlers import RotatingFileHandler
from requests.auth import HTTPDigestAuth

log = logging.getLogger("")
log.setLevel("DEBUG")
# LOG_FILE = "/var/log/pushbullet.log"
LOG_FILE = "pushbullet.log"
logformat = logging.Formatter("%(levelname)s %(asctime)s (%(name)s) %(message)s")

def send(msg):
    log.info("pushbullet message: " + str(msg))

    # pushbullet api token stuff
    pbtoken = "o.vw5MjjLvdjB7pgOguRDRlpgqwLKfxdJi"
    pburl = "https://api.pushbullet.com/v2/pushes"

    # set some session headers
    session = requests.Session() # for pushbullet api calls
    session.headers.update({"Accept": "application/json", "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
    session.headers.update({"Access-Token": pbtoken})
    
    pbdata = '{"type": "note", "title":"' + msg[0] + '", "body":"' + msg[1] + '"}'
    
    # send message
    try:
        request = session.post(pburl, data=pbdata)
        log.debug("pushbullet response = " + str(request))
        if request.status_code == 400:
            log.error("error stuff")
            pbdata = '{"type": "note", "title":"Sort Error", "body":"script hit an error in sending"}'
            request = session.post(pburl, data=pbdata)
    except Exception as e:
        log.error("error sending message: " + str(msg) + " - error:" + str(e))