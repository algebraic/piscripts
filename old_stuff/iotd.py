#!/usr/bin/env python3

import requests
import random
import os
import mimetypes
import sys
import pathlib
import ctypes
from urllib.parse import urlparse

url = "https://www.reddit.com/r/wallpapers.json?limit=100"
# url = "https://www.reddit.com/r/wallpaper.json"
# ?&limit=100

headers = {"User-agent": "Zach\'s Test Script"}
# folder = "C:\\Users\\johnsonz2\\Downloads\\bg-test\\"
folder = "/home/pi/Pictures/"

# response = requests.get(url)
response = requests.get(url, headers=headers)


# exit if there's any error in get
if not response.ok:
    print("Error", str(response.status_code) + " - " + response.reason)
    sys.exit()


# get an array of posts in the page
array_of_posts = response.json()['data']['children']
# print("array_of_posts = " + str(array_of_posts))

# print all urls
# for post in array_of_posts:
#     print(post['data']['url'] + " -- " + pathlib.Path(post['data']['url']).suffix)

# get number of posts
number_of_posts = str(len(array_of_posts))
print("number_of_posts = " + str(number_of_posts))

# get random number between 1 and the total number of posts
random_number = random.randint(1, int(number_of_posts))
print("random_number = " + str(random_number))

# get random post from array of posts
random_post = array_of_posts[random_number]['data']
# print("random_post = " + str(random_post))

# get the image url of the first post
image_url = random_post['url']
print("image title: " + random_post['title'])
print("image_url = " + image_url)

# get file extension
ext = pathlib.Path(image_url).suffix
print("ext = " + ext)

# grab image
image = None
try:
    image = requests.get(image_url, headers=headers)
except requests.ConnectionError as e:
   # handle the exception
    print("Error: " + str(e.args[0].args[0]))
    sys.exit(1)

if (image != None and image.status_code == 200):
    try:
        file_loc = folder + random_post['title'] + ext
        output_filehandle = open(file_loc, mode='bx')
        output_filehandle.write(image.content)
        # set desktop background - windows
        # ctypes.windll.user32.SystemParametersInfoW(20, 0, file_loc, 0)
        # set desktop background - rpi
        os.system("pcmanfm --set-wallpaper '" + file_loc + "'")
    except AttributeError as e:
        print("uh-oh, error")
        print(e)
        pass

# fix for linux and maybe handle duplicates and junk...

for i in range(range):
    print(i)