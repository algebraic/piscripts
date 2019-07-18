#!/usr/bin/env python3

import urllib.request, json, requests
from subprocess import call
import pushbullet

response = requests.get("https://api.github.com/repos/algebraic/piscripts/contents")
githublist = json.loads(response.text)

exclude = [
    ".gitignore",
    "README.md",
    "web"
]

for item in githublist:
    if item["name"] not in exclude:
        name = item["name"]
        call(['bash', '/home/pi/scripts/download.sh', name])

pushbullet.send(["GitHub Download","Scripts have been downloaded from GitHub"])