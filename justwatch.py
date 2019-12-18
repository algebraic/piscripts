#!/usr/bin/env python3

import logging, sys
from justwatch import JustWatch
from logging import handlers
from logging.handlers import RotatingFileHandler

# only allow single instance
windows = False
try:
    import socket
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    ## Create an abstract socket, by prefixing it with null. 
    s.bind( '\0postconnect_gateway_notify_lock') 
except socket.error as e:
    error_code = e.args[0]
    error_string = e.args[1]
    print("Process already running (%d:%s ). Exiting" % ( error_code, error_string))
    sys.exit (0)
except AttributeError as ae:
    print("probably running on windows...")
    windows = True

# rest of logging caught by calling script
log = logging.getLogger("")

# stdout handler
logformat = logging.Formatter("%(levelname)s %(asctime)s (%(name)s) %(message)s")
ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(logformat)
log.addHandler(ch)

def find(name):
    log.debug("searching for '" + name + "'")

    just_watch = JustWatch(country='US')

    results = just_watch.search_for_item(providers=['nfx'], query=name)

    log.debug("(results=" + str(len(results["items"])) + ")")

    for item in results["items"]:
        if item["title"].casefold() == name.casefold():
            log.info("yay, found it:: " + item["title"])
            return True

# find('6 underground')