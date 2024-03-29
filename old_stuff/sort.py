#!/usr/bin/env python3

'''
a python media manager
Using TMDb api for data - themoviedb.org

changelog
03052019 - added a season offset capability like episode offset (for talking dead)
04052019 - put all this junk in github :)
08142019 - using Unidecode (https://pypi.org/project/Unidecode/) to handle episode/movie names with special characters
11192021 - adding an always-delete feature, like for 'RARBG_DO_NOT_MIRROR.exe' kinda crap
11222021 - ^-- always deleting *.nfo, folders were lying around otherwise


todo
# check if something is on netflix before downloading?
# see about omitting previously caught confusing files and skip them subsequently if they're still around?
# consolidate all messages into a single output at the end, just set variables along the way?

# search do-over, omit year on movie or maybe try a year+-1
    ^ for when downloaded movies have the wrong year... like "No Retreat No Surrender 1985 DVDRip DivX-DKB24.mp4" (actually from 1986)

# add a thing to delete stuff like "sample" and crap like that

weird episode titles to check:
    Marvel's Agents of S.H.I.E.L.D. S03E05 4,722 Hours.mp4

weird movie titles...
I think it's just looking for \d{4} for year, but like "Bladerunner 2049 (2017)" totally screws it up...
maybe change that to look for \(\d{4}\) -- ONLY within parenthesis -- in case a title has a year in it

multipart episodes may need some work...
currently if both episodes have the same name then it's renamed to
    'Marvels Agents of SHIELD S05E01-E02 - Orientation (1-2).mkv'
if names are different then it catches both titles

known issue: deleting valid files when show incorrectly matches
		- as with Legit
             Legit (Jim Jefferies) matches with a BBC show by the same name, non-matched episodes
             in season 1 appear to have just been deleted... That shouldn't happen

get the tvdb api stuff into a separate module
maybe logging junk too?
'''

import requests, os, re, json, logging, sys, errno, shutil, smtplib, argparse, time
import simplepush
from pathlib import Path
from requests.auth import HTTPDigestAuth
from os.path import join, getsize
from logging import handlers
from logging.handlers import RotatingFileHandler
from unidecode import unidecode

# only allow single instance
windows = False
try:
    import socket
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    ## Create an abstract socket, by prefixing it with null. 
    s.bind( '\0postconnect_gateway_notify_lock') 
except socket.error as e:
    error_code = e.args[0]
    error_string = e.args[1]
    print("Process already running (%d:%s ). Exiting" % ( error_code, error_string))
    sys.exit (0)
except AttributeError as ae:
    print("probably running on windows...")
    windows = True

# set logging
log = logging.getLogger("")
LOG_FILE = "/var/log/sort.log"
if windows:
    LOG_FILE = "sort.log"
logformat = logging.Formatter("%(levelname)s %(asctime)s (%(name)s) %(message)s")
##DEBUG (debug stuff & extra stuff from urllib3.connectionpool)
##INFO (regular sort operations)
##WARNING (can't find show, episode, movie...)
##ERROR (just errors)
##CRITICAL (problems with an api or filename confusion)

# stdout handler
# ch = logging.StreamHandler(sys.stdout)
# ch.setFormatter(logformat)
# log.addHandler(ch)
# ^^^ adding the stdout handler here duplicates log output
# file handler
fh = handlers.RotatingFileHandler(LOG_FILE, maxBytes=(1048576*5), backupCount=7)
fh.setFormatter(logformat)
log.addHandler(fh)

# read config file
try:
    with open('/home/pi/piscripts/sort.config.json') as json_data_file:
        data = json.load(json_data_file)
except FileNotFoundError as e:
    print("Config file not found, try windows path")
    try:
        with open('sort.config.json') as json_data_file:
            data = json.load(json_data_file)
    except FileNotFoundError as e:
        msg = "Sort config file not found, aborting"
        log.error(msg)
        sys.exit (0)

# set logging level
log = logging.getLogger("")
if (data):
    log.setLevel(data["config"]["logLevel"])
else:
    log.setLevel("DEBUG")

# function to check if a path is valid
def dir_path(string):
    if os.path.isdir(string):
        return string
    else:
        raise NotADirectoryError(string)

# command line switches
parser = argparse.ArgumentParser()
parser.add_argument("-q", "--quiet", help="run sort without notifications", action="store_true")
parser.add_argument("-o", "--overwrite", help="run sort in overwrite mode, any existing files will be overwritten", action="store_true")
parser.add_argument("-d", "--debug", help="set sort logging level to DEBUG", action="store_true")
parser.add_argument("-t", "--test", help="run in test mode, don't actually move anything", action="store_true")

# alternate path
parser.add_argument("-p", "--path", help="specify alternate source folder", type=dir_path)

# arguments from deluge execute plugin
parser.add_argument("torrent_id", nargs="?", default="")
parser.add_argument("torrent_name", nargs="?", default="")
parser.add_argument("save_path", nargs="?", default="")
args = parser.parse_args()

# notification - optional setting to email/text when a file is moved or sort encounters an error
notify = data["advanced"]["notifications"]["notify"]
# check commandline switch
#  or windows
if args.quiet:
    notify = False
# hard-code quiet if you're downloading a bunch of crap...
# notify = False

if args.debug:
    log.setLevel(logging.DEBUG)
    
# overwrite - optional setting to overwrite existing files
overwrite = data["config"]["overwrite"]
overwrite_msg = ""
# check commandline switch
if args.overwrite:
    overwrite = True
if overwrite:
    overwrite_msg = " (OVERWRITE ENABLED)"

# function to replace special characters
def stripChars(string):
    separator = "-"
    return re.sub(r'[^\w^\'^\(^\)\-_\. &,:]', separator, string)

# set folders
if windows:
    source_dir = data["config"]["win_src"]
    tv_dir = data["config"]["win_tv"]
    movie_dir = data["config"]["win_movie"]
else:
    source_dir = data["config"]["pi_src"]
    tv_dir = data["config"]["pi_tv"]
    movie_dir = data["config"]["pi_movie"]

# check for alternate source
if args.path:
    source_dir = args.path
    log.debug("using alternate source folder: " + args.path)
    
print("### args.path = " + str(args.path))

log.debug("~~~ begin sorting" + overwrite_msg + ": start checking source folder ~~~")
log.info("sort starting")

# check if paths are valid
try:
    dir_path(source_dir)
except NotADirectoryError as e:
    log.error("Folder doesn't exist: " + str(e))
    sys.exit (0)

# crawl dirs and look up stuff
for root, dirs, files in os.walk(source_dir, topdown=True):
    mediaFound = False
    skipped = False
    folder = root
    log.debug("checking folder " + folder)

    # skip sending messages if there's gonna be a ton of 'em
    tooManyMessages = False
    if len(files) > 4:
        log.info("")
        tooManyMessages = True
        msg = ["Heads Up", "Processing " + str(len(files)) + " files from " + str(root.split(os.path.sep)[-2]) + os.path.sep + str(root.split(os.path.sep)[-1]), "newSeason"]
        log.info(str(msg))
        simplepush.ppushitrealgood(msg, notify)

    for name in files:
        # check extensions first
        ext = Path(name).suffix.strip()
        tmdbname = ""
        if ext in data["config"]["mediaExts"]:
            # login w/tvdb api key and get token
            #################################################################################################################################
            url = "https://api.thetvdb.com/login"
            params = '{"apikey": "F4B2F3D661A7D2CD"}'
            s = requests.Session() # for tvdb/tmdb api calls
            s.headers.update({"Accept": "application/json", "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
            r = s.post(url, data=params)

            # check for errors from tvdb api
            if "Response [5" in str(r):
                log.error(str(r))
                if not tooManyMessages:
                    simplepush.ppushitrealgood(["TVDB API Error", str(r) + "Unable to sort media at this time. " + str(name)])
                sys.exit (0)

            tvdbToken = json.loads(r.text)["token"]
            s.headers.update({"Authorization": "Bearer " + tvdbToken})

            # TMDb api key
            tmdbapi = "ce283f8ff68c019530c5f5ccf045de2d"
            # if you don't already have one, create an account and register an api key here - https://www.themoviedb.org/settings/api
            #################################################################################################################################

            log.debug("found a media file, " + name)
            mediaFound = True
            deleteFolder = root
            cleanname = re.sub(r'\.', " ", os.path.splitext(name)[0]).strip()

            # modify name for search if necessary - prolly just hard-code junk here as needed, it's just for borked filenames like this
            # cleanname = cleanname.replace("S1981 E14", "S02E01")

            log.debug("file cleanname: '" + cleanname + "'")

            ##########################################################################################
            ## differentiate between tv show and movie::
            ## try to extract season/episode info from filename
            ## -- try 'S##E##-E##' first, then '##x##' - can add more variants as needed
            ## (-^ that second -E## is for multipart episodes, the E is optional)
            ## if epdata still winds up as None, treat it as a movie
            ##########################################################################################
            epdata = re.search(r'(S(\d+)E(\d+)(?:-E(\d{2})|-(\d{2}))?)', cleanname, re.IGNORECASE)
            if (str(epdata) == "None"):
                epdata = re.search(r'((\d{2})X(\d{2})(?:-E(\d{2})|-(\d{2}))?)', cleanname, re.IGNORECASE)

            if (str(epdata) == "None"):
                # it's a movie
                log.debug("file '" + cleanname + "' looks like a movie")
                try:
                    yr = re.search(r'[\(|\[|" "](\d{4})[\)|\]|" "]', cleanname, re.IGNORECASE)
                    title = cleanname.split(yr.group(0), 1)[0].strip()
                    year = yr.group(1)
                    log.debug("movie year=" + str(year))
                    log.debug("movie title=" + str(title))
                except AttributeError:
                    year = None
                    title = None
                    mediaFound = False
                    msg = ["Sort Error", "Can't parse movie name/year for " + name, "sortError"]
                    log.warning(str(msg))
                    if not tooManyMessages:
                        log.info(str(msg))
                        simplepush.ppushitrealgood(msg, notify)
                    continue

                # using themoviedb api for movies
                # zj: see about omitting year?
                url = "https://api.themoviedb.org/3/search/movie?api_key=" + tmdbapi + "&query=" + str(title).replace(" ", "+") + "&year=" + str(year)

                log.debug("themoviedb url: " + str(url))
                r = s.get(url)
                
                movielist = None
                
                try:
                    if r.status_code != 200:
                        msg = ["Sort Error", "Unable to query TMDb", "sortError"]
                    else:
                        movielist = json.loads(r.text)
                except json.decoder.JSONDecodeError:
                    msg = ["Sort Error", "themoviedb JSONDecodeError", "sortError"]
                except AttributeError:
                    msg = ["Sort Error", "themoviedb AttributeError", "sortError"]
                except NameError:
                    msg = ["Sort Error", "themoviedb NameError", "sortError"]
                except Exception:
                    msg = ["Sort Error", "themoviedb Exception", "sortError"]

                movie = None
                if movielist is None:
                    error = json.loads(r.text)
                    errormsg = ["Sort Error (" + str(r.status_code) + ")","themoviedb returned null for " + str(title) + " " + str(year), "sortError"]
                    log.error(msg[1] + " (code " + str(r.status_code) + ")")
                    msg = errormsg
                    mediaFound = False
                else:
                    # tmdb check
                    if movielist["total_results"] > 0:
                        if movielist["total_results"] == 1:
                            movie = movielist["results"][0]
                        else:
                            # check titles
                            for i in movielist["results"]:
                                log.debug("checking movie title '" + str(i["title"]) + "' - id = " + str(i["id"]))
                                if (title.lower() == i["title"].lower()):
                                    movie = i
                                    break

                    testmode = ""            
                    if movie is not None:

                        if title.lower() != movie["title"].lower():
                            # just an fyi check, as with "This Is Your Death"/"The Show", working title/actual title - warn in case of name changes
                            log.info("Sort name discrepancy, name in file is different than tmdb name: '" + title + "' vs '" + movie["title"] + "' - https://www.themoviedb.org/movie/" + str(movie["id"]))
                            
                        log.debug("movie appears to be '" + movie["title"] + "' - https://www.themoviedb.org/movie/" + str(movie["id"]))
                        # if movie path doesn't exist, create it
                        if not os.path.exists(movie_dir):
                            log.warning("creating folder " + movie_dir)
                            os.makedirs(movie_dir)

                        # rename & move file
                        newname = stripChars(movie["title"]) + " (" + year + ")"

                        try:
                            destFile = os.path.join(movie_dir, newname + ext)
                            moveit = True
                            if (os.path.exists(destFile) and not overwrite):
                                moveit = False
                            
                            if moveit:
                                if args.test:
                                    testmode = "TEST MODE: "
                                else:
                                    shutil.copy(os.path.join(root, name), destFile)

                                if ext == '.srt':
                                    msg = [testmode + "Subtitles Available", "Subtitles added for " + str(newname), "newMedia"]
                                else:
                                    overview = str(unidecode(movie["overview"]))
                                    url = "https://www.themoviedb.org/movie/" + str(movie["id"])
                                    msg = [testmode + "New Movie: " + newname, url, "newMedia"]
                                    if data["advanced"]["notifications"]["verbose-movies"]:
                                        msg[1] = overview + " " + url
                            else:
                                msg = [testmode + "Sort Duplicate", "Skipping folder, file already exists: " + str(destFile).replace("\\","\\\\"), "duplicateMedia"]
                                mediaFound = False
                                skipped = True
                                if not tooManyMessages:
                                    log.warning(str(msg))
                                    simplepush.ppushitrealgood(msg, notify)
                                continue
                        except OSError as e:
                            msg = [testmode + "Sort Error", "Error " + str(e.errno) + " (" + str(e.errno == errno.ENOENT) + ")", "sortError"]
                            log.error(str(msg))
                            log.error(e)
                            raise
                    else:
                        msg = [testmode + "Sort Error", "Can't find movie '" + str(title) + "' in TMDb", "sortError"]
                        mediaFound = False
                        log.warning(str(msg))

                if not tooManyMessages:
                    log.info(str(msg))
                    simplepush.ppushitrealgood(msg, notify)
                    
            else:
                # it's a tv show
                log.debug("file '" + cleanname + "' looks like a tv show")

                # check if it's a multipart episode
                multipart = True if bool(epdata.group(4)) else False
                
                try:
                    log.debug("epdata: '" + epdata.group(1) + "'")
                    showname = cleanname.split(epdata.group(1), 1)[0].strip()
		            # if filename ends with - remove it
                    if showname.endswith("-"):
                        showname = showname[:-1].strip()

                    log.debug("show name: '" + showname + "'")

                    s_num = str(int(epdata.group(2))).strip()
                    # pad to invlude a leading zero if < 10
                    if len(str(s_num)) == 1:
                        s_num = str(0) + str(s_num)
                    log.debug("season: '" + s_num + "'")

                    e_num = str(int(epdata.group(3))).strip()
                    # pad to invlude a leading zero if < 10
                    if len(str(e_num)) == 1:
                        e_num = str(0) + str(e_num)
                    log.debug("episode: '" + e_num + "'")
                    
                    if multipart:
                        e_num2 = str(int(epdata.group(4))).strip()
                        log.debug("File '" + cleanname + "' is a multipart episode - " + e_num + " & " + e_num2)
                except AttributeError:
                    showname = "can't parse show name"
                    s_num = "can't parse season number"
                    e_num = "can't parse episode number"

                # check if using replaced name
                isReplaced = False
                for key in data["nameReplace"].keys():
                    if showname.lower() == key.lower():
                        log.debug("replacing show name '" + str(showname) + "' with '" + str(data["nameReplace"].get(key)) + "'")
                        showname = data["nameReplace"].get(key)
                        isReplaced = True

                # check if using forced tvdb id
                isForced = False
                showid = None
                for key in data["forceId"].keys():
                    if showname.lower() == key.lower():
                        # set showid and tmdbname accordingly
                        showid = data["forceId"].get(key)
                        tmdbname = key
                        log.debug("using show id " + showid + " for " + showname)
                        isForced = True

                if isForced is False:
                    # query show from name
                    url = "https://api.thetvdb.com/search/series?name=" + showname
                    log.debug("searching tvdb for '" + showname + "' (" + url + ")")

                    r = s.get(url)
                    showlist = json.loads(r.text)
                    if "Error" in showlist:
                        msg = ["Sort Error", "Can't find show name for '" + showname + "', try searching on tvdb manually", "sortError"]
                        log.warning(str(msg))
                        if not tooManyMessages:
                            simplepush.ppushitrealgood(msg, notify)
                        mediaFound = False
                        continue
                    elif "data" in showlist and len(showlist["data"]) > 1:
                        # multiple matching shows, check if show name has an exact match
                        for show in showlist["data"]:
                            if showname.lower() == str(show["seriesName"]).lower():
                                showid = show["id"]
                                showname = show["seriesName"]
                                isReplaced = True
                                log.debug("multiple shows found, it appears to be " + str(show["seriesName"]) + " (" + str(showid) + ")")
                                break

                        if showid is None:
                            msg = ["Sort Error", "Can't find exact show name for '" + showname + "' - " + str(len(showlist["data"])) + " shows found, try replacing name or forcing id", "sortError"]
                            log.warning(str(msg))
                            if not tooManyMessages:
                                simplepush.ppushitrealgood(msg, notify)
                            mediaFound = False
                            continue
                    else:
                        showid = showlist["data"][0]["id"]
                    # use name replacement if specified
                    if isReplaced is True and tmdbname == "":
                        tmdbname = stripChars(showname)
                    else:
                        tmdbname = stripChars(showlist["data"][0]["seriesName"])

                # check for episode offset
                if tmdbname in data["advanced"]["offset"]["episode"]:
                    offset = data["advanced"]["offset"]["episode"][tmdbname]
                    log.debug("offsetting " + tmdbname + " episode numbers by " + str(offset))
                    e_num = int(e_num) + int(offset)
                
                # check for season offset
                if tmdbname in data["advanced"]["offset"]["season"]:
                    offset = data["advanced"]["offset"]["season"][tmdbname]
                    log.debug("offsetting " + tmdbname + " season numbers by " + str(offset))
                    s_num = int(s_num) + int(offset)

                # get show episode from tvdb by showid
                if not isForced:
                    log.debug ("show id: " + str(showid))
                url = "https://api.thetvdb.com/series/" + str(showid) + "/episodes/query?airedSeason=" + str(s_num) + "&airedEpisode=" + str(e_num)
                log.debug("query url:" + url)
                r = s.get(url)
                r2 = None
                episode2Info = None
                url2 = None
                ep2name = None

                # if multipart episode, also grab part 2's name
                if multipart:
                    url2 = "https://api.thetvdb.com/series/" + str(showid) + "/episodes/query?airedSeason=" + str(s_num) + "&airedEpisode=" + str(e_num2)
                    log.debug("query url for multipart second episode: " + url2)
                    r2 = s.get(url2)

                if r.status_code != 200 or (bool(r2) and r2.status_code != 200):
                    # show isn't queryable, some bit of info is off
                    msg = ["Sort Error", "TVDB returned a " + str(r.status_code) + " for " + str(tmdbname) + ", problem with showid (" + str(showid) + "), season num (" + str(s_num) + "), or episode num (" + str(e_num) + ")", "sortError"]
                    log.warning(str(msg))
                    if not tooManyMessages:
                        simplepush.ppushitrealgood(msg, notify)
                    #log.warning("tvdb returned a 404 for " + str(tmdbname) + ", problem with showid (" + str(showid) + "), season # (" + str(s_num) + "), or episode # (" + str(e_num) + ")")
                    mediaFound = False
                    continue
                else:
                    episodeInfo = json.loads(r.text)
                    if bool(r2):
                        episode2Info = json.loads(r2.text)

                # rebuild S##E## in case of offset
                epdata_str = "S" + str(s_num).zfill(2) + "E" + str(e_num).zfill(2)
                # if multipart, append second episode number
                epdata_str = epdata_str + "-E" + str(e_num2).zfill(2) if multipart else epdata_str
                
                # put rename variables together
                epname = episodeInfo["data"][0]["episodeName"]
                # if multipart, check titles of both episodes
                log.debug("episode name:" + epname)
                episodeName = epname
                if bool(episode2Info):
                    ep2name = episode2Info["data"][0]["episodeName"]
                    log.debug("multipart, episode 2 name:" + ep2name)
                    if re.sub(r"\(\d\)", "", epname).strip().lower() == re.sub(r"\(\d\)", "", ep2name).strip().lower():
                        # episodes have the same name but number in parentheses, like "Orientation (1)" and "Orientation (2)", just add both numbers
                        episodeName = re.sub(r"\(\d\)", "", epname).strip() + " (" + str(e_num) + "-" + str(e_num2) + ")"
                    else:
                        # episodes have different names, add both names
                        episodeName = epname + "-" + ep2name

                # fix any weird characters in episode title
                episodeName = str(unidecode(episodeName))
                
                shortname = tmdbname + " " + epdata_str + " - " + str(unidecode(episodeName))
                log.debug("shortname = " + shortname)
                
                newname = shortname + ext
                
                path = os.path.join(re.sub(r'[^\w^\'^\(^\)\-_\. &,]', '', tmdbname), "Season " + str(s_num) + os.path.sep)
                newname = re.sub(r'[^\w^\'^\(^\)\-_\.\: &,]', '-', newname) # replace special characters with underscore
                log.debug("renaming file to '" + newname + "'")

                # if show/season path doesn't exist, create it
                log.info("### args.test = " + str(args.test))
                if not args.test:
                    if not (os.path.exists(os.path.join(tv_dir, path))):
                        log.debug("creating folders: " + path)
                        os.makedirs(os.path.join(tv_dir, path))

                # rename & move file
                testmode = ""
                try:
                    destFile = os.path.join(tv_dir+path+newname)
                    moveit = True
                    if (os.path.exists(destFile) and not overwrite):
                        moveit = False

                    if moveit:
                        if args.test:
                            testmode = "TEST MODE: "
                        else:
                            shutil.copy(os.path.join(root, name), os.path.join(tv_dir+path+newname))

                        url = "https://www.thetvdb.com/?tab=episode&seriesid=" + str(showid) + "&seasonid=" + str(episodeInfo["data"][0]["airedSeasonID"]) + "&id=" + str(episodeInfo["data"][0]["id"])

                        msg = [testmode + "New Episode of " + tmdbname, epdata_str + " - " + episodeName + " - " + url, 'newMedia']

                        # check if show is set to verbose
                        verbosetv = data["advanced"]["notifications"]["verbose-tv"]
                        if verbosetv or (not verbosetv and tmdbname in data["advanced"]["notifications"]["shows_list"]):
                            # get show url on tmdb from tvdb id
                            tmdburl = "https://api.themoviedb.org/3/find/" + str(showid) + "?api_key=" + tmdbapi + "&language=en-US&external_source=tvdb_id"
                            r = s.get(tmdburl)
                            tmdblist = json.loads(r.text)
                            tmdbid = tmdblist["tv_results"][0]["id"]

                            # get show's TMDb id for notification link
                            url = "https://www.themoviedb.org/tv/" + str(tmdbid) + "/season/" + str(s_num) + "/episode/" + str(e_num)
                            overview = str(unidecode(episodeInfo["data"][0]["overview"]))
                            # note - overview field from tvdb can contain unicode characters - message gets encoded as utf-8 in send function
                            msg[1] = epdata_str + " - " + episodeName + " \"" + overview + "\" " + url
                    else:
                        msg = [testmode + "Sort Duplicate", "File already exists: " + str(destFile).replace("\\","\\\\"), "duplicateMedia"]
                    
                    if not tooManyMessages:
                        log.info(str(msg))
                        simplepush.ppushitrealgood(msg, notify)
                except OSError as e:
                    msg = [testmode + "Sort Error", "Error " + str(e.errno) + " (" + str(e.errno == errno.ENOENT) + ")", "sortError"]
                    log.error(str(msg))
                    if not tooManyMessages:
                        simplepush.ppushitrealgood(msg, notify)
                    log.error(e)
                    raise
        else:
            log.debug("skipping " + ext + " file - '" + name + "'")

    if not skipped:
        if not mediaFound:
            log.debug("skipping folder, no media identified")
        elif folder != source_dir and data["config"]["cleanup"] is True and not args.test:
            log.debug("seriously, stop deleting stuff")

log.debug("~~~ sort completed, happy watching ~~~")
log.debug("=================")