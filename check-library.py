#!/usr/bin/env python3
'''
check library script

any unmatched media (junk using a screenshot instead of a poster, easiest visual identifier)
anything containing "rarbg" crap in metadata?
also maybe a count of any junk still in the completed folder?
perhaps change the raspicheck scripts to send a pushbullet notification for stuff like ip address?
'''

import requests, os, re, json, logging, sys, errno, shutil, smtplib, argparse, time, subprocess, hurry.filesize, sqlite3
from pathlib import Path
from requests.auth import HTTPDigestAuth
from os.path import join, getsize
from logging import handlers
from logging.handlers import RotatingFileHandler
from sqlite3 import Error
from hurry.filesize import size

# database connection
#database = "C:\\Users\\johnsonz2\\Downloads\\com.plexapp.plugins.library.db"
database = "/storage/torrents/plexdata/Library/Application Support/Plex Media Server/Plug-in Support/Databases/com.plexapp.plugins.library.db"

# set logging
log = logging.getLogger("")
log.setLevel(logging.INFO)
LOG_FILE = "/var/log/checklibrary.log"
logformat = logging.Formatter("%(levelname)s %(asctime)s (%(name)s) %(message)s")
##DEBUG (debug stuff & extra stuff from urllib3.connectionpool)
##INFO (regular sort operations)
##WARNING (can't find show, episode, movie...)
##ERROR (just errors)
##CRITICAL (problems with an api or filename confusion)

# stdout handler
ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(logformat)
log.addHandler(ch)
# file handler
fh = handlers.RotatingFileHandler(LOG_FILE, maxBytes=(1048576*5), backupCount=7)
fh.setFormatter(logformat)
log.addHandler(fh)

log.info("~~~ start library check ~~~")
log.info("=================")

# only allow single instance
try:
    import socket
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    ## Create an abstract socket, by prefixing it with null. 
    s.bind( '\0postconnect_gateway_notify_lock') 
except socket.error as e:
    error_code = e.args[0]
    error_string = e.args[1]
    log.error("Process already running (%d:%s ). Exiting" % ( error_code, error_string))
    sys.exit (0) 
except AttributeError as ae:
    log.error("attribute error...probably running on windows")
    log.error(ae)

# command line switches
parser = argparse.ArgumentParser()
parser.add_argument("-q", "--quiet", help="run sort without notifications", action="store_true")
parser.add_argument("-d", "--debug", help="set sort logging level to DEBUG", action="store_true")
args = parser.parse_args()

# notification - optional setting to email/text when a file is moved or sort encounters an error
notify = True
# check commandline switch
if args.quiet:
    notify = False

if args.debug:
    log.setLevel(logging.DEBUG)
    
# set some session headers
s1 = requests.Session() # for pushbullet api calls
s1.headers.update({"Accept": "application/json", "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
log.debug(s1.headers)
    
if notify:
    # pushbullet block
    pbtoken = "o.vw5MjjLvdjB7pgOguRDRlpgqwLKfxdJi"
    pburl = "https://api.pushbullet.com/v2/pushes"

# function to send messages
def send(msg):
    log.debug("send function (" + str(msg) + ")")
    if notify:
        log.debug("sending notification")
        pbdata = '{"type": "note", "title":"' + msg[0] + '", "body":"' + msg[1] + '"}'
        s1.headers.update({"Access-Token": pbtoken})
        try:
            log.debug("trying to hit pushbullet...")
            r1 = s1.post(pburl, data=pbdata)
            log.debug("pushbullet response = " + str(r1))
            if r1.status_code == 400:
                log.debug("error stuff")
                pbdata = '{"type": "note", "title":"Sort Error", "body":"script hit an error in sending"}'
                r1 = s1.post(pburl, data=pbdata)
        except Exception as e:
            log.error("error sending message: " + str(msg) + " - error:" + str(e))

# check for rarbg junk
######################################################################################################################
output = ""
try:
    log.debug("trying connection")
    conn = sqlite3.connect(database)
    with conn:
        cur = conn.cursor()
        cur.execute("select title from metadata_items where lower(title) like '%rarbg%'")
        rows = cur.fetchall()
        for row in rows:
            log.info(row[0])
            output += row[0] + "\\n"
except Error as e:
    log.error("uh-oh, error: " + str(e))

if len(rows) > 0:
    msg = str(len(rows)) + " item(s) found containing 'rarbg' junk:\\n" + output
else:
    msg = "No 'rarbg' pollution found in library"

log.info(msg)
message = ["Plex Library Check", msg]
send(message)

# check for unmatched media
######################################################################################################################
cur.execute("select id, title, guid from metadata_items where lower(guid) like '%local%'")
rows = cur.fetchall()

for row in rows:
    log.info("unmatched item: " + str(row[1]) + " (" + str(row[0]) + ")")
    output += str(row[1]) + " (" + str(row[0]) + ")\\n"

if len(rows) > 0:
    msg = str(len(rows)) + " unmatched item(s) found:\\n" + output
else:
    msg = "No unmatched items found in library"

log.info(msg)
message = ["Plex Library Check", msg]
send(message)

# try some filesystem space stuff
######################################################################################################################
df = subprocess.Popen(["df", "--si", "/storage/plex"], stdout=subprocess.PIPE)

output = df.communicate()[0]
output = output.decode("utf-8")

one, two, three, four, five, six, seven, device, size, used, available, percent, mountpoint = \
    output.split()

sizepart = "Total size: " + size + "\\n"
sizepart += "Used: " + used + " (" + percent + ")\\n"
sizepart += "Free: " + available

log.info("Plex library disk: " + device)
log.info("Total size: " + size)
log.info("Used: " + used)
log.info("Percent used: " + percent)
log.info("Free: " + available)


msg = ["Plex Library Check", sizepart]
send(msg)

# all done
######################################################################################################################
log.info("=================")
log.debug("~~~ all done ~~~")
