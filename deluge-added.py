#!/usr/bin/env python3
import sys, argparse, logging, re, os
import pushbullet
from logging import handlers
from logging.handlers import RotatingFileHandler

# set logging
log = logging.getLogger("")
log.setLevel("INFO")
LOG_FILE = "/var/log/deluge-added.log"
# LOG_FILE = "deluge-complete.log"
logformat = logging.Formatter("%(levelname)s %(asctime)s (%(name)s) %(message)s")

# stdout handler
ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(logformat)
log.addHandler(ch)
# file handler
fh = handlers.RotatingFileHandler(LOG_FILE, maxBytes=(1048576*5), backupCount=7)
fh.setFormatter(logformat)
log.addHandler(fh)

log.debug("starting deluge-added.py")

parser = argparse.ArgumentParser()
parser.add_argument("torrent_id", nargs="?", default="")
parser.add_argument("torrent_name", nargs="?", default="")
parser.add_argument("save_path", nargs="?", default="")
args = parser.parse_args()

if args.torrent_id:
    log.debug("deluge-added: args.torrent_id: " + args.torrent_id)
if args.torrent_name:
    log.debug("deluge-added: args.torrent_name: " + args.torrent_name)
if args.save_path:
    log.debug("deluge-added: args.save_path: " + args.save_path)

if (args.torrent_name == ""):
    log.debug("no torrent name, don't do anything")
    sys.exit (0)

# check to make sure it's not a whole season
cleanname = re.sub(r'\.', " ", args.torrent_name).strip()
epdata = re.search('(S(\d+)E(\d+)(?:-E(\d{2})|-(\d{2}))?)', cleanname, re.IGNORECASE)

if (epdata == None):
    log.debug("doesn't seem to have episode data, check for full season...")
    epdata = re.search('(S(\d+) )', cleanname, re.IGNORECASE)
    if (epdata != None):
        log.debug("yup, " + args.torrent_name + " seems to be an entire season...")
        try:
            os.popen("deluge-console pause " + args.torrent_id)
            log.info("paused full-season torrent: " + args.torrent_name)
            pushbullet.send(["Warning: entire season added", args.torrent_name + "\\nTorrent paused, go double check that"])
            sys.exit (0)
        except Exception as e:
            pushbullet.send(["ERROR: unable to pause", args.torrent_name + "\\nTorrent can't be paused, you should probably check that out"])
            log.error("error: " + str(e))

log.info("passed torrent " + args.torrent_name)