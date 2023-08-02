#!/usr/bin/env python3
import os, shutil, subprocess

dir_path = "/mnt/torrents/completed/"
dst_path = "/mnt/torrents/completed/moving/"

count = 0
# Iterate directory
for path in os.listdir(dir_path):
    # check if current path is a file
    if os.path.isfile(os.path.join(dir_path, path)):
        print("path = " + path)
        # shutil.copy(os.path.join(dir_path, path), dst_path)
        count += 1

print("moving " + str(count) + " files")

