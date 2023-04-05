#!/usr/bin/env python3
import logging
from logging import handlers
import os

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
fh = handlers.RotatingFileHandler("/var/log/wyzecam.log", "a", 5242880, 7)
fh.setFormatter(logformat)
log.addHandler(fh)

hostname = '192.168.86.57' #example
response = os.system("ping " + hostname)
if response == 0:
  log.debug(hostname, 'cam is up!')
else:
  log.debug(hostname, 'cam is down!')