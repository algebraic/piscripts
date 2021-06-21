#!/bin/bash

TARGET=/storage/torrents/completed/

inotifywait -m -e moved_to $TARGET \
        | while read FILENAME
                do
			sort
                done
