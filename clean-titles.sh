sqlite3 "/storage/torrents/plexdata/Library/Application Support/Plex Media Server/Plug-in Support/Databases/com.plexapp.plugins.library.db"
select id, title from metadata_items where lower(title) like '%rarbg%';

# thing for pulling list of all titles
# 
# sqlite3 -header -separator $'\t' "/storage/torrents/plexdata/Library/Application Support/Plex Media Server/Plug-in Support/Databases/com.plexapp.plugins.library.db" "select quote(id), quote(title) from metadata_items;" > data.csv
# 
# for removing periods
# 
# update metadata_items set title = REPLACE(title, '.', ' ') where id in (list, of, ids);
# 
# for finding underscores
# 
# select id, title from metadata_items where title like '%\_%' ESCAPE '\';
