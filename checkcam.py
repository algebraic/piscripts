#!/usr/bin/env python3
import logging
import platform
import subprocess
import sys
import simplepush
from logging import handlers

# set logging
log = logging.getLogger()
log.setLevel(logging.DEBUG)
logformat = logging.Formatter("%(levelname)s %(asctime)s (%(name)s) %(message)s")

fh = handlers.RotatingFileHandler("wyzecam.log", maxBytes=(1048576*5), backupCount=7)
fh.setFormatter(logformat)
log.addHandler(fh)


class cam:
    def __init__(self, name, ip_address):
        self.name = name
        self.ip_address = ip_address


hosts = [
    cam("driveway", "192.168.86.57"),
    cam("deck", "192.168.86.22"),
    cam("living room", "192.168.86.25")
]
max_attempts = 4

# Loop through the hosts
for host in hosts:
    # Loop through the number of attempts allowed
    for attempt in range(1, max_attempts + 1):
        # Ping the IP address using the subprocess module
        ping_process = subprocess.Popen(['ping', '-c', '1', host.ip_address], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        ping_output, _ = ping_process.communicate()

        # Check the exit code of the ping command
        if ping_process.returncode == 0:
            log.info(f"Successfully pinged {host.name} cam on attempt {attempt}.")
            break  # Stop attempting if ping was successful
        else:
            log.debug(f"Ping attempt {attempt} failed. Retrying...")

            # Perform action if this is the last attempt
            if attempt == max_attempts:
                msg = ["Camera Offline", {host.name} + " cam seems to be offline", ""]
                simplepush.ppushitrealgood(msg, True)
                log.warning(f"Failed to ping {host.name} cam after {max_attempts} attempts.")