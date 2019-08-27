#!/usr/bin/env python3

import pushbullet, subprocess
from subprocess import call

call(['bash', '/home/pi/scripts/backup-data.sh'])

pushbullet.send(["Backup script ran", "Plex and Deluge metadata have been backed up to /storage/external/backup"])