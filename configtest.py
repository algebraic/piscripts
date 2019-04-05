#!/usr/bin/env python3

import json

print("ok, let's see...")

try:
    with open('sort.config.json') as json_data_file:
        data = json.load(json_data_file)
except FileNotFoundError as e:
    print("FileNotFoundError")

try:
    data
except NameError:
    print("data not found")
else:
    for key in data["nameReplace"].keys():
        print(key)

    # ext = ".mp4"
    # if ext in data["mediaExts"]:
    #     print("woot")
    # else:
    #     print("nope")

    # print("data[nameReplace]")
    # print(data["nameReplace"])


    # print("data[forceId]")
    # print(data["forceId"])
    # print("data[epOffset]")
    # print(data["epOffset"])
    # print("data[seasonOffset]")
    # print(data["seasonOffset"])
    # print("data[verboseShows]")
    # print(data["verboseShows"])

    # print("=================")
    # print("test:")
    # print(data["nameReplace"]["Legit"])
    # print("=================")
    # print("test 2:")
    # for key in data["nameReplace"].keys():
    #     print(key + " = " + data["nameReplace"][key])