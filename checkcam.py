#!/usr/bin/env python3
import logging
from logging import handlers
import platform
import subprocess
import sys
import simplepush


# set logging
log = logging.getLogger()
log.setLevel(logging.INFO)
#LOG_FILE = "checkiplog.txt"
logformat = logging.Formatter("%(levelname)s %(asctime)s (%(name)s) %(message)s")

# stdout handler
ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(logformat)
log.addHandler(ch)
# file handler
#fh = handlers.RotatingFileHandler("checkiplog.txt", maxBytes=(1048576*5), backupCount=7)
fh = handlers.RotatingFileHandler("/var/log/wyzecam.log", maxBytes=(1048576*5), backupCount=7)
# fh = handlers.RotatingFileHandler("/var/log/wyzecam.log", "a", 5242880, 7)
fh.setFormatter(logformat)
log.addHandler(fh)

def ping(host):
    log.debug("ping function: " + str(host))
    print("ping function: " + str(host))

    param = '-n' if platform.system().lower()=='windows' else '-c'
    command = ['ping', param, '1', host]
    result = subprocess.run(command, stdout=subprocess.PIPE)
    
    log.debug("result: " + str(result))
    print("result: " + str(result))
    
    output = result.stdout.decode('utf8')
    if "Request timed out." in output or "100% packet loss" in output:
        msg = ["Camera Offline", "cam " + str(host) + " seems to be offline"]
        simplepush.ppushitrealgood(msg, True)
        return "NOT CONNECTED"
    
    msg = ["Camera Online", "yay, cam " + str(host) + " is online"]
    simplepush.ppushitrealgood(msg)
    return "CONNECTED"

hostname = '192.168.86.57' #example
# response = os.system("ping " + hostname)
# if response == 0:
#   print(hostname, 'cam is up!')
# else:
#   print(hostname, 'cam is down!')
output = ping(hostname)
print("output = " + str(output))
log.debug("output = " + str(output))


