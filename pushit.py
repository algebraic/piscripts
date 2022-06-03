#!/usr/bin/env python3
import logging
import requests
import argparse
import sys
import json
import urllib.parse
import urllib.request
from logging import handlers
from logging.handlers import RotatingFileHandler
from requests.auth import HTTPDigestAuth

# rest of logging caught by calling script
log = logging.getLogger("")

# stdout handler
logformat = logging.Formatter(
    "%(levelname)s %(asctime)s (%(name)s) %(message)s")
ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(logformat)
log.addHandler(ch)

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
        msg = "Sort config file not found, aborting (from ppushitrealgood.py)"
        log.error(msg)
        sys.exit(0)


def ppushitrealgood(msg, notify=True):
    if not notify:
        log.info("** quiet mode, no messages **")

    simplepush_url = data["advanced"]["notifications"]["simplepush-url"]
    simplepush_key = data["advanced"]["notifications"]["simplepush-key"]
    # final_url_parsed = ""
    # https://api.simplepush.io/send/wL86KC/wow/so%20simple

    try:
        # assemble message parameters
        # title = msg[0]
        # body = msg[1]
        title = "title1"
        body = "message1"

        # final_url = simplepush_url + simplepush_key + "/" + title + "&c=" + content + "&u=" + url
        # final_url_parsed = simplepush_url + simplepush_key + "/" + urllib.parse.quote_plus(title,safe="") + "/" + urllib.parse.quote_plus(body,safe="")
        # log.debug("### final_url_parsed: " + final_url_parsed)
        
        # zj: from python example at https://simplepush.io/
        msgdata = urllib.parse.urlencode({'key': simplepush_key, 'title': title, 'msg': body, 'event': 'testevent1'}).encode()
        req = urllib.request.Request(simplepush_url, data=msgdata)
        #################################################################
        theactualurl = req.full_url
        params = req.data
        log.debug("### req url: " + str(theactualurl))
        #https://api.simplepush.io/send/
        log.debug("### req params: " + str(params))
        #b'key=wL86KC&title=TEST+MODE%3A+New+Episode+of+Peacemaker&msg=S01E01+-+A+Whole+New+Whirled%5CnAfter+making+a+miraculous+recovery%2C+Peacemaker+returns+home-only+to+discover+that+his+freedom+comes+at+a+price.%5Cnhttps%3A%2F%2Fwww.themoviedb.org%2Ftv%2F110492%2Fseason%2F01%2Fepisode%2F01&event=testevent1'

        # body = str(msg[1]).split("\\n")
        # content = body[0]
        # url = body[1]
        # final_url = simplepush_url + simplepush_key + "/" + title + "&c=" + content + "&u=" + url
        # final_url_parsed = simplepush_url + simplepush_key + "&t=" + urllib.parse.quote_plus(title,safe="") + "&c=" + urllib.parse.quote_plus(content,safe="") + "&u=" + urllib.parse.quote_plus(url,safe="")

        if notify:
            log.debug("attempting to send message...")
            urllib.request.urlopen(req)
            # req.urlopen(req)
    except IndexError as e:
        log.error(str(e))
        log.error(msg)

    # # set some session headers
    # session = requests.Session()
    # session.headers.update({"Accept": "application/json", "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})

    # # send message
    # if notify:
    #     try:
    #         #urllib.request.urlopen(req)

    #         # zj: testing now
    #         request = session.post("https://api.simplepush.io/send/wL86KC/TEST1/S01E01/event/testevent1")
    #         log.debug("### pushit response = " + str(request))
    #         # request = session.post(final_url_parsed)
    #         # log.debug("pushit response = " + str(request))
    #         # if request.status_code == 400:
    #         #     log.error("error code 400, retrying...")
    #         #     request = session.post(final_url_parsed)
    #         #     if request.status_code == 400:
    #         #         # pbdata = '{"type": "note", "title":"Sort Error", "body":"script hit an error in sending"}'
    #         #         # request = session.post(pburl, data=pbdata)
    #         #         log.error("still failed...")
    #     except Exception as e:
    #         log.error("###error sending message: " + str(msg) + "\n### error:" + str(e))
