# piscripts
scripts for various pi stuff


# declare media file extensions (csv file extensions)
# if you want to keep subtitle files make sure their extensions are included here (.srt or whatever)


# show name replacements (used for both the filename and the folder structure)
# nameReplace = {
#     "DC's Legends of Tomorrow":"Legends of Tomorrow",
#     "DCs Legends of Tomorrow":"Legends of Tomorrow",
#     "Saturday Night Live":"SNL",
#     "Last Week Tonight":"Last Week Tonight",
#     "The Flash 2014":"The Flash",
#     "The Flash (2014)":"The Flash",
#     "Marvel's Agents of S H I E L D":"Marvel's Agents of SHIELD",
#     "Marvels Agents of S H I E L D":"Marvel's Agents of SHIELD",
#     "Heartland CA":"Heartland",
#     "Heartland (2007) (CA)":"Heartland",
#     "The Clone Wars":"Star Wars: The Clone Wars",
#     "The Clone Wars -":"Star Wars: The Clone Wars",
#     "Star Wars- The Clone Wars":"Star Wars: The Clone Wars",
#     "Riverdale US":"Riverdale",
#     "Legit":"Legit (2013)",
#     "Greys Anatomy":"Grey's Anatomy",
#     "Will - Grace":"Will & Grace"
# }
'''
So, show name replacements...
Use this when a show can't be found on tvdb with its original file name, or if you just don't like how a show name appears.
    - omitting the "DC's" from Legends of tomorrow, or the "(2014)" from The Flash
    - keeping "Last Week Tonight" as just "Last Week Tonight" (tvdb wants to throw "with John Oliver" behind it)
    - changing "Saturday Night Live" to the more succinct "SNL"
Note - if you change the file name to something tvdb doesn't recognize, you'll also have to force the show id for the modified name (as is the case for SNL or The Flash)
You just run it like this - "show name you get":"show name you want"
'''


# force show id's
forceId = {
    "Scandal":"248841",
    "SNL":"76177",
    "The Flash":"279121",
    "Heartland":"82701",
    "Splitting Up Together":"328595",
    "Timeless":"311713",
    "Will & Grace":"71814",
    "Transformers":"72499",
    "Marvel's Agents of SHIELD":"263365",
    "Green Lantern":"251807",
    "Friends":"79168",
    "Legends of Tomorrow":"295760"
}
'''
So, forcing show id's...
Use this when tvdb can't find a show. Usually this will be something like with Scandal, where there's a whole bunch of matching shows...
If we don't find exactly one match, you'll get a warning in the log. Then just hop onto tvdb and find the specific show you want, and toss its id up there.
You can think of it as manually linking a show name with a tvdb show id.

'''


# episode number offset
epOffset = {
    "SNL":0,
}

'''
So, episode number offset...
Sometimes episode numbers get skewed, like in season 43 of Saturday Night Live...
The episode with Larry David was uploaded as S43E06, because the uploader was counting the two specials in that season as numbered episodes - it was actually episode 4, not 6.
Since S43E06 is actually Chance the Rapper, and is listed so on tvdb, that episode winds up misnamed.
If you download via a service like ShowRSS, once that happens you'll probably get consistently misnumbered episodes for the rest of the season.
Use this to correct that, increment episode numbers by whatever amount is specified - usage is "show name":# to offset by
Note - if you force a show name, use your forced name instead of the given name
'''


# season number offset
seasonOffset = {
    "Talking Dead":-1,
}

'''
So, season number offset...
Same thing as with episode numbers, just for season numbers. Thanks, Talking Dead...  ;)
'''


# verbose output (booleans for all movies and all shows, csv list for individual show names)
verboseMovies = True
verboseShows = False
verboseShows_list = {
    "The Flash",
    "Gotham",
    "Legends of Tomorrow",
    "Arrow",
    "Grey's Anatomy"
}
'''
So, verbose output...
If you have notification messages enabled, these settings can include some extra info about the item being moved.
The notification messages will include links to TMDb page for movies, and episode descriptions as well as a link for shows.
The booleans will set ALL movies or ALL tv shows to verbose. If verboseShows = False, then only entries in verboseShows_list will be set to verbose.
Note - for the list use the *final* name of the tv show, either the official name from TMDb or your own replaced name
'''


# optional cleanup, delete non-media files and remove folders (True/False)
# setting to True WILL DELETE any remaining files not of the types listed in mediaExts and remove the folder
# setting to False will leave any files/folders in place
cleanup = True


