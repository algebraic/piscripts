#!/bin/bash

# download & fix Eyesort script
curl -s -H 'Accept:application/vnd.github.v3.raw' https://api.github.com/repos/algebraic/piscripts/contents/sort.py -o /home/vpn/sort.py
sudo chmod 777 /home/vpn/sort.py
sudo dos2unix /home/vpn/sort.py

# download & fix pushbullet script
curl -s -H 'Accept:application/vnd.github.v3.raw' https://api.github.com/repos/algebraic/piscripts/contents/pushbullet.py -o /home/vpn/pushbullet.py
sudo chmod 777 /home/vpn/pushbullet.py
sudo dos2unix /home/vpn/pushbullet.py

# download & fix Deluge-added script
curl -s -H 'Accept:application/vnd.github.v3.raw' https://api.github.com/repos/algebraic/piscripts/contents/deluge-added.py -o /home/vpn/deluge-added.py
sudo chmod 777 /home/vpn/deluge-added.py
sudo dos2unix /home/vpn/deluge-added.py