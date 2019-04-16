#!/usr/bin/env python3

import requests, sys

# pushbullet api
token = "o.vw5MjjLvdjB7pgOguRDRlpgqwLKfxdJi"
url = "https://api.pushbullet.com/v2/pushes"

s = requests.Session()

if len(sys.argv) > 1:
    #deluge variables
    torrent_id = sys.argv[1]
    torrent_name = sys.argv[2]
    save_path = sys.argv[3]
else:
    torrent_name = "testing pushbullet (vpn)"

data = '{"type": "note", "title":"Torrent Added", "sender_name":"Deluge", "body":"' + torrent_name + '"}'
s.headers.update({"Access-Token": token, "Accept": "application/json", "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
r = s.post(url, data=data)

