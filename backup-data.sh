#!/bin/bash

# backup plex metadata folders

TIME=`date +%b-%d-%y`
FILENAME=backup-$TIME.tar.gz

# source backup folders
PLEXDIR='/storage/torrents/plexdata/Library/Application Support/Plex Media Server'
DELUGEDIR='/home/vpn/.config/deluge'

DESDIR=/storage/external/backup

tar -cvpzf $DESDIR/plex-$FILENAME "$PLEXDIR/Media" "$PLEXDIR/Metadata" "$PLEXDIR/Plug-ins" "$PLEXDIR/Plug-in Support" "$PLEXDIR/Preferences.xml"
tar -cvpzf $DESDIR/plex-$FILENAME "$PLEXDIR/Preferences.xml"
tar -cvpzf $DESDIR/deluge-$FILENAME "$DELUGEDIR/"

# plex is really too big to upload...
#gdrive upload $DESDIR/plex-$FILENAME --parent 0B_2nZwHTghv-aGZaQi1rLTRPMjg --delete
#gdrive upload $DESDIR/deluge-$FILENAME --parent 0B_2nZwHTghv-aGZaQi1rLTRPMjg --delete
