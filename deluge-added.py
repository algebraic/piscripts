#!/usr/bin/env python3
import sys, argparse, logging, re, os, subprocess
import pushbullet
from logging import handlers
from logging.handlers import RotatingFileHandler

# set logging
log = logging.getLogger("")
log.setLevel("INFO")
LOG_FILE = "/var/log/deluge-added.log"
logformat = logging.Formatter("%(levelname)s %(asctime)s (%(name)s) %(message)s")

# stdout handler
ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(logformat)
# log.addHandler(ch)
# file handler
fh = handlers.RotatingFileHandler(LOG_FILE, maxBytes=(1048576*5), backupCount=7)
fh.setFormatter(logformat)
log.addHandler(fh)

parser = argparse.ArgumentParser()
parser.add_argument("torrent_id", nargs="?", default="")
parser.add_argument("torrent_name", nargs="?", default="")
parser.add_argument("save_path", nargs="?", default="")
args = parser.parse_args()

log.debug("starting deluge-added.py")

if args.torrent_id:
    log.debug("deluge-added: args.torrent_id: " + args.torrent_id)
if args.torrent_name:
    log.debug("deluge-added: args.torrent_name: " + args.torrent_name)
if args.save_path:
    log.debug("deluge-added: args.save_path: " + args.save_path)

if (args.torrent_name == ""):
    log.debug("no torrent name, don't do anything")
    sys.exit(0)

# function to pause torrent
def stopTorrent(msg):
    try:
        cmd = "deluge-console pause " + args.torrent_id
        subprocess.run(cmd.split(), check=True, text=True)
        log.info("paused full-season torrent: " + args.torrent_name)
        pushbullet.send(["Warning: torrent paused", msg])
        sys.exit(0)
    except Exception as e:
        pushbullet.send(["ERROR: unable to pause", args.torrent_name + "\\nTorrent can't be paused, you should probably check that out"])
        log.error("error: " + str(e))

# check to make sure it's not a whole season
cleanname = re.sub(r'\.', " ", args.torrent_name).strip()
epdata = re.search('(S(\d+)E(\d+)(?:-E(\d{2})|-(\d{2}))?)', cleanname, re.IGNORECASE)

if (epdata != None):
    log.debug("has episode data, check for duplicate...")
    log.debug("cleanname = " + cleanname)
    log.debug("epdata = " + str(epdata))
    # ok, so checking for dups is going to be involved...let's notify for proper's instead for now...
    if (re.search('proper', cleanname, re.IGNORECASE)):
        # it's a 'proper' replacement dl
        log.warning("'proper' downloaded: " + cleanname)
        pushbullet.send(["'PROPER' downloaded:", args.torrent_name + "\\nCheck if the 'proper' download replaces something."])
else:
    log.debug("doesn't seem to have episode data, check for full season...")
    epdata = re.search('(S(\d+) )', cleanname, re.IGNORECASE)
    if (epdata != None):
        log.debug("yup, " + args.torrent_name + " seems to be an entire season...")
        stopTorrent(args.torrent_name + " seems to be an entire season")
        sys.exit(0)
    else:
        # check if it's on netflix
        log.debug("might be a movie, check for '" + cleanname + "' on netflix...")
        yr = re.search('[\(|\[|" "](\d{4})[\)|\]|" "]', cleanname, re.IGNORECASE)
        log.debug("yr = " + str(yr))
        if (yr != None):
            title = cleanname.split(yr.group(0), 1)[0].strip()
            year = yr.group(1)
            log.debug("movie year=" + str(year))
            log.debug("movie title=" + str(title))
        else:
            log.debug("can't parse title/year from '" + cleanname + "'")
        # finish this ^
        # also maybe check that it's not already in the library?

log.info("passed torrent " + args.torrent_name)