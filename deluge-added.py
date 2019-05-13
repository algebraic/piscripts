#!/usr/bin/env python3
import sys, argparse, logging, checklib, pushbullet
from subprocess import call
from logging import handlers
from logging.handlers import RotatingFileHandler

# set logging
log = logging.getLogger("")
log.setLevel("DEBUG")
# LOG_FILE = "/var/log/deluge-added.log"
LOG_FILE = "deluge-complete.log"
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

# call("checklib.py", shell=False)
# checklib.testthing()
pushbullet.send(["torrent added",args.torrent_name])