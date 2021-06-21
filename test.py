#!/usr/bin/env python3
import logging, subprocess, sys
from logging import handlers

# set logging
log = logging.getLogger("")
log.setLevel("DEBUG")
LOG_FILE = "/var/log/deluge-added.log"
# LOG_FILE = "C:\\stuff\\deluge-added.log"
logformat = logging.Formatter("%(levelname)s %(asctime)s (%(name)s) %(message)s")

# stdout handler
ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(logformat)
# log.addHandler(ch)
# file handler
fh = handlers.RotatingFileHandler(LOG_FILE, maxBytes=(1048576*5), backupCount=7)
fh.setFormatter(logformat)
log.addHandler(fh)

torrent_id = "2fa71a2dbb7d53a39373a9c4e2c9d89aaa7a6db1"
try:
    cmd = "deluge-console pause " + torrent_id
    subprocess.run(cmd.split(), check=True, text=True)
    print("yay, all done")
    log.info("yay, all done")
except Exception as e:
    print("exception:: " + str(e))
    log.warning("exception: " + str(e))