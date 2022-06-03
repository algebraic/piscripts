import json
import logging
import sys
from urllib import request, parse

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

    if notify:
        try:
            # assemble message parameters
            t = msg[0]
            b = msg[1]
            e = msg[2]
            log.debug("attempting to send message...")
            msgdata = parse.urlencode({'key': simplepush_key, 'title': t, 'msg': b, 'event': e}).encode()
            req = request.Request(simplepush_url, data=msgdata)
            log.debug(request.urlopen(req));
        except IndexError as e:
            log.error(str(e))
            log.error(msg)