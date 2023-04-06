#!/usr/bin/env python3
import logging, platform, subprocess, sys, simplepush
from logging import handlers

# set logging
log = logging.getLogger()
log.setLevel(logging.INFO)
logformat = logging.Formatter("%(levelname)s %(asctime)s (%(name)s) %(message)s")

fh = handlers.RotatingFileHandler("logs/wyzecam.log", maxBytes=(1048576*5), backupCount=7)
fh.setFormatter(logformat)
log.addHandler(fh)

ip_address = "192.168.86.57"  # Replace with the IP address you want to ping
max_attempts = 3          # Maximum number of attempts to ping the IP address

# Loop through the number of attempts allowed
for attempt in range(1, max_attempts + 1):
    # Ping the IP address using the subprocess module
    ping_process = subprocess.Popen(['ping', '-c', '1', ip_address], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ping_output, _ = ping_process.communicate()

    # Check the exit code of the ping command
    if ping_process.returncode == 0:
        log.debug("Successfully pinged {ip_address} on attempt {attempt}.")
        break  # Stop attempting if ping was successful
    else:
        log.debug("Ping attempt {attempt} failed. Retrying...")

        # Perform action if this is the last attempt
        if attempt == max_attempts:
            msg = ["Camera Offline", "driveway cam seems to be offline", ""]
            simplepush.ppushitrealgood(msg, True)
            log.warning("Failed to ping {ip_address} after {max_attempts} attempts.")