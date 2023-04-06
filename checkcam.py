#!/usr/bin/env python3
import logging, platform, subprocess, sys, simplepush
from logging import handlers

# set logging
log = logging.getLogger()
log.setLevel(logging.INFO)
logformat = logging.Formatter("%(levelname)s %(asctime)s (%(name)s) %(message)s")

# stdout handler
ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(logformat)
log.addHandler(ch)
# file handler
fh = handlers.RotatingFileHandler("/var/log/wyzecam.log", maxBytes=(1048576*5), backupCount=7)
fh.setFormatter(logformat)
log.addHandler(fh)

def ping(host):
    log.debug("ping function: " + str(host))

    param = '-n' if platform.system().lower()=='windows' else '-c'
    command = ['ping', param, '1', host]
    result = subprocess.run(command, stdout=subprocess.PIPE)
    
    log.debug("result: " + str(result))
    
    output = result.stdout.decode('utf8')
    if "Request timed out." in output or "100% packet loss" in output:
        msg = ["Camera Offline", "driveway cam seems to be offline", ""]
        simplepush.ppushitrealgood(msg, True)
        return "OFFLINE"
    
    # msg = ["Camera Online", "yay, cam " + str(host) + " is online", ""]
    # simplepush.ppushitrealgood(msg, True)
    return "online"

hostname = '192.168.86.57'
output = ping(hostname)
log.info("driveway cam " + str(output))