#!/bin/bash

# download file from url & fix stuff
curl -s -H 'Accept:application/vnd.github.v3.raw' https://api.github.com/repos/algebraic/piscripts/contents/$1 -o /home/vpn/$1
sudo chmod 777 /home/vpn/$1
sudo dos2unix /home/vpn/$1