#!/usr/bin/env python3
import sys, argparse, logging, re, os, subprocess
import pushbullet
from logging import handlers
from logging.handlers import RotatingFileHandler

# set logging
log = logging.getLogger("")
log.setLevel("DEBUG")
LOG_FILE = "/var/log/deluge-added.log"
# LOG_FILE = "C:\\stuff\\deluge-added.log"
logformat = logging.Formatter("%(levelname)s %(asctime)s (%(name)s) %(message)s")

# stdout handler
ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(logformat)
log.addHandler(ch)
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

log.warning("this would be the whole command line thing...")
log.warning("/home/pi/scripts/deluge-added.py " + args.torrent_id + " " + args.torrent_name + " " + args.save_path)

# function to pause torrent
def stopTorrent(msg):
    try:
        log.debug("attempting to pause torrent " + args.torrent_name)
        log.debug("args.torrent_id: " + args.torrent_id)
        log.debug("## this is the pause command...")
        log.debug("## sudo -u vpn -i -- deluge-console -c /home/vpn/.config/deluge/ pause " + args.torrent_id)

        # os.popen("sudo -u vpn -i -- deluge-console -c /home/vpn/.config/deluge/ pause " + args.torrent_id)

        subprocess.run("sudo -u vpn -i -- deluge-console pause " + args.torrent_id, shell=True, check=True)

        # ok, so something is fucked in here, it won't pause crap when it's added, but running it manually seems to work...
        # it's catching an exception, the "unable to pause error" thing below here

        # subprocess.run("sudo -u vpn -i -- deluge-console -c /home/vpn/.config/deluge/ pause " + test_id, shell=True, check=True)

        log.debug("paused full-season torrent: " + args.torrent_name)
        pushbullet.send(["Warning: torrent paused", msg])
        sys.exit(0)
    except Exception as e:
        pushbullet.send(["ERROR: unable to pause", args.torrent_name + "\\nTorrent can't be paused, you should probably check that out"])
        log.error("error: " + str(e))

# check to make sure it's not a whole season
cleanname = re.sub(r'\.', " ", args.torrent_name).strip()
epdata = re.search('(S(\d+)E(\d+)(?:-E(\d{2})|-(\d{2}))?)', cleanname, re.IGNORECASE)

if (epdata == None):
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
        log.debug("yr = " + yr)
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