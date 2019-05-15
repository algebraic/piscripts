#!/usr/bin/env python3

import urllib.request, json, requests
from subprocess import call

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
        call(['bash', '/home/vpn/download.sh', name])

