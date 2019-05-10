#!/usr/bin/env python3

import requests, os, re, json, logging, sys, errno, shutil, smtplib, argparse, time
from pathlib import Path
from requests.auth import HTTPDigestAuth
from os.path import join, getsize
from logging import handlers
from logging.handlers import RotatingFileHandler

# set logging
log = logging.getLogger("")
log.setLevel("INFO")
LOG_FILE = "/var/log/checklib.log"
#LOG_FILE = "checklib.log"
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

# pushbullet stuff
pbtoken = "o.vw5MjjLvdjB7pgOguRDRlpgqwLKfxdJi"
pburl = "https://api.pushbullet.com/v2/pushes"

# set some session headers
s1 = requests.Session() # for pushbullet api calls
s1.headers.update({"Accept": "application/json", "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})

notify = True
# function to send messages
def send(msg):
    if (notify):
        log.info("send function (" + str(msg) + ")")
        pbdata = '{"type": "note", "title":"' + msg[0] + '", "body":"' + msg[1] + '"}'
        s1.headers.update({"Access-Token": pbtoken})
        try:
            log.debug("trying to hit pushbullet...")
            r1 = s1.post(pburl, data=pbdata)
            log.debug("pushbullet response = " + str(r1))
            if r1.status_code == 400:
                log.debug("error stuff")
                pbdata = '{"type": "note", "title":"Sort Error", "body":"script hit an error in sending"}'
                r1 = s1.post(pburl, data=pbdata)
        except Exception as e:
            log.error("error sending message: " + str(msg) + " - error:" + str(e))

# arguments from deluge execute plugin
parser = argparse.ArgumentParser()
parser.add_argument("torrent_id", nargs="?", default="")
parser.add_argument("torrent_name", nargs="?", default="")
parser.add_argument("save_path", nargs="?", default="")
args = parser.parse_args()

msg = ["test message","testing stuff out"]
log.info(msg)
send(msg)