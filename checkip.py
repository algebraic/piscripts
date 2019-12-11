#!/usr/bin/env python3
'''
check ip address script

check vpn ip address and restart it if it's died
'''

import requests, os, re, json, logging, sys, errno, shutil, smtplib, argparse, time, subprocess, ast, timeout_decorator, datetime
from pathlib import Path
from requests.auth import HTTPDigestAuth
from os.path import join, getsize
from logging import handlers
from logging.handlers import RotatingFileHandler
import sqlite3
from sqlite3 import Error

# set logging
log = logging.getLogger()
log.setLevel(logging.INFO)
#LOG_FILE = "checkiplog.txt"
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
#fh = handlers.RotatingFileHandler("checkiplog.txt", maxBytes=(1048576*5), backupCount=7)
fh = handlers.RotatingFileHandler("/var/log/checkip.log", "a", 5242880, 7)
fh.setFormatter(logformat)
log.addHandler(fh)

log.debug("~~~ start ip check ~~~")
log.debug("=================")

# only allow single instance
try:
    import socket
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    # Create an abstract socket, by prefixing it with null.
    s.bind('\0postconnect_gateway_notify_lock')
except socket.error as e:
    error_code = e.args[0]
    error_string = e.args[1]
    log.error("Process already running (%d:%s ). Exiting" % (error_code, error_string))
    sys.exit(0)
except AttributeError as ae:
    log.error("attribute error...probably running on windows")
    log.error(ae)

# command line switches
parser = argparse.ArgumentParser()
parser.add_argument("-q", "--quiet", help="run without notifications", action="store_true")
parser.add_argument("-d", "--debug", help="set logging level to DEBUG", action="store_true")
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


# function to return ip address
@timeout_decorator.timeout(10, timeout_exception=StopIteration)
def getIp(bashCommand):
     try:
          process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
          output, error = process.communicate()
          ip = ast.literal_eval(output.decode()).get("ip")
          return ip
     except:
          log.error("timeout?")
          return "null"

# check regular pi ip address
######################################################################################################################
if notify:
    bashCommand = "curl ipinfo.io --max-time 10 --connect-timeout 10"
    ip1 = getIp(bashCommand)
    log.info("regular user ip address: " + ip1)

# check vpn ip address
######################################################################################################################
bashCommand = "sudo -u vpn -i -- curl ipinfo.io --max-time 10 --connect-timeout 10"
ip2 = getIp(bashCommand)
log.info("vpn ip address: " + ip2)

if ip2 == "null":
     # restart vpn
     log.warning("vpn ip is null, restarting!")

    # possibility of dns problem...remember that whole thing?
    # maybe check sudo nano /etc/systemd/resolved.conf
    # sudo systemctl restart systemd-resolved

     restartCmd = "sudo systemctl restart openvpn deluged deluge-web"
     restartprocess = subprocess.Popen(restartCmd.split(), stdout=subprocess.PIPE)
     o, e = restartprocess.communicate()
     log.info("output: " + str(o))
     log.info("error: " + str(e))
     msg = ["VPN ip was null", "Restarted vpn & deluge services.\\n\\n" + str(datetime.datetime.now())]
else:
     # send stuff
     if notify:
         msg = ["IP Address Check", "Raspberry Pi ip address: " + ip1 + "\\nVPN ip address: " + ip2]
         
send(msg)

# all done
######################################################################################################################
# alldonemsg = ["Check Ran", "IP Check ran at " + str(datetime.datetime.now())]
# send(alldonemsg)
log.debug("=================")
log.debug("~~~ all done ~~~")
