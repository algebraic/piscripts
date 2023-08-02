#!/usr/bin/env python3

import argparse
import json
import logging
import os
import re
import shutil
from pathlib import Path
from urllib import parse, request

import requests

# multi-part episodes

# piscripts/brand_new_sort.py -p cp/'My.Adventures.with.Superman.S01E04.1080p.WEB.h264-EDITH[eztv.re].mkv'
# piscripts/brand_new_sort.py -p cp/'My.Adventures.with.Superman.S01E05.1080p.WEB.h264-EDITH[TGx]'
# piscripts/brand_new_sort.py -p cp/The.Office.Extended.Cut.720p.10bit.WEBRip.x265-budgetbits
# piscripts/brand_new_sort.py -p cp/'Unknown Cave Of Bones (2023) [1080p] [WEBRip] [5.1] [YTS.MX]'
#piscripts/brand_new_sort.py -p cp/'The Office (US) (2005) Season 1-9 S01-S09 (1080p BluRay x265 HEVC 10bit AAC 5.1 Silence)'/'Season 1'/'The Office (US) (2005) - S01E01 - Pilot (1080p BluRay x265 Silence).mkv'
def setup_logging():
    log_file = "/home/pi/piscripts/brand_new_sort.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s (%(funcName)s) %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    # Create a file handler and add it to the root logger
    file_handler = logging.FileHandler(log_file)
    # file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter("%(asctime)s - %(levelname)s (%(funcName)s) %(message)s")
    file_handler.setFormatter(file_formatter)
    logging.getLogger().addHandler(file_handler)
    return logging.getLogger()

tooManyMessages = False
# simplepush notifications
def ppushitrealgood(msg):
    global tooManyMessages
    logger.info(f"tooManyMessages = {tooManyMessages}")
    sp_key = "wL86KC"
    sp_url = "https://api.simplepush.io/send"
    if not tooManyMessages:
        try:
            # assemble message parameters
            msg_title = msg[0]
            msg_body = msg[1]
            msg_event = msg[2]
            logger.debug("attempting to send message...")
            msgdata = parse.urlencode({'key': sp_key, 'title': f'{msg_title}', 'msg': f'{msg_body}', 'event': f'{msg_event}'}).encode()
            req = request.Request(sp_url, data=msgdata)
            logger.debug(request.urlopen(req));
        except IndexError as e:
            logger.error({e})
            logger.error(f"error sending message: {msg}")

# save searched ids to cut down on api calls
def save_cache_to_file(cache_dict, file_path):
    with open(file_path, "w") as file:
        json.dump(cache_dict, file)
def load_cache_from_file(file_path):
    try:
        with open(file_path, "r") as file:
             # Check if the file is empty
            if not file.read(1):
                return {}
            # Reset the file pointer back to the beginning
            file.seek(0)
            return json.load(file)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def copy_file(file, type, file_name):
    # fix source path for copy
    source_path = args.path
    if args.path.startswith("cp/"):
        source_path = f"/mnt/torrents/completed/{args.path[3:]}"
    if not os.path.isfile(f'{source_path}'):
        # directory-torrents need the media filename appended back
        source_path += f"/{Path(file).name}"
    logger.debug(f"source_path = '{source_path}' -- isfile:{os.path.isfile(f'{source_path}')} -- exists: {os.path.exists(f'{source_path}')}")

    # set destination path
    destination_path = ""
    if type == "tv":
        # include show & season folders
        destination_path = f"/mnt/tv/{file_name}"
    elif type == "movie":
        destination_path = f"/mnt/movies/{file_name}"
    logger.debug(f"destination_path = '{destination_path}' -- exists:{os.path.exists(f'{destination_path}')}")
    
    # sanity check & copy file
    if os.path.isfile(f'{source_path}') and os.path.exists(f'{source_path}') and not os.path.exists(f'{destination_path}'):
        try:
            os.makedirs(os.path.dirname(f'{destination_path}'), exist_ok=True)
            logger.debug(f"shutil.copy('{source_path}', '{destination_path}')")
            
            #output = shutil.copy(f'{source_path}', f'{destination_path}')
            output = "testing"
            
            msg = ["new stuff", f"new media file: {output}", "newStuff"]
        except FileExistsError as e:
            logger.error(e)
            logger.error(":/")
            msg = ["ERROR", f"error trying to copy '{source_path}' to '{destination_path}", "fileError"]
        finally:
            logger.debug(f"copy result:: '{output}'")
    else:
        logger.warning(f"file already exists in destination: {destination_path}")
        msg = ["duplicate", f"file already exists in destination: {destination_path}", "duplicateMedia"]

    # send simplepush notification
    ppushitrealgood(msg)

def search_movie(file):
    filename = Path(file).name
    ext = Path(file).suffix.strip()
    logger.debug(f"search movies for: {filename}")
    try:
        yr = re.search(r'[\(|\[|" "|\.](\d{4})[\)|\]|" "|\.]', filename, re.IGNORECASE)
        title = filename.split(yr.group(0), 1)[0].strip().replace(".", " ")
        year = yr.group(1)
        logger.debug(f"movie: {title} ({year})")
        url = "https://api.themoviedb.org/3/search/movie"

        headers = {
            "accept": "application/json",
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJjZTI4M2Y4ZmY2OGMwMTk1MzBjNWY1Y2NmMDQ1ZGUyZCIsInN1YiI6IjVhMjVhNTczYzNhMzY4MGI5ZDBkNTU0NyIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.vFgkfokmICq00bnxaVuPxpNbPuC_SonBW_acltEUm5U"
        }
        params = {
            "query": title,
            "year": year
        }
        response = requests.get(url, headers=headers, params=params)
        jsonlist = json.loads(response.text)
        tmdb_name = jsonlist['results'][0]['title']
        year = jsonlist['results'][0]['release_date'][:4]
        final_file_name = f"{tmdb_name} ({year}){ext}"
        logger.info(f"final file name: '{final_file_name}'")
        copy_file(file, "movie", final_file_name)
    except AttributeError:
        logger.warning(f"can't parse movie name/year for: {filename}")


def check_show_id(showname):
    cache_file_path = "/home/pi/piscripts/show_id_cache.json"
    show_id_cache = load_cache_from_file(cache_file_path)

    for n in show_id_cache:
        logger.debug(f"\t*** showname:: '{n}' | {show_id_cache[n]}")
         
    if showname in show_id_cache:
        # return id saved locally
        logger.debug(f"returning local id: {show_id_cache[showname][1]}")
        return f"{show_id_cache[showname][1]}"
    else:
        logger.debug(f"can't find '{showname}' in cache, lookup on tmdb")

    # otherwise lookup show id from tmdb & save it
    url = "https://api.themoviedb.org/3/search/tv"

    headers = {
        "accept": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJjZTI4M2Y4ZmY2OGMwMTk1MzBjNWY1Y2NmMDQ1ZGUyZCIsInN1YiI6IjVhMjVhNTczYzNhMzY4MGI5ZDBkNTU0NyIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.vFgkfokmICq00bnxaVuPxpNbPuC_SonBW_acltEUm5U"
    }
    params = {
        "query": f"{showname}"
    }
    
    try:    
        response = requests.get(url, headers=headers, params=params)
        jsonlist = json.loads(response.text)
        logger.info(f"total_results = {jsonlist['total_results']}")
        if (jsonlist['total_results'] == 0):
            return 0
        tmdb_name = jsonlist['results'][0]['name']
        tmdb_id = jsonlist['results'][0]['id']
        logger.debug(f"returning tmdb id: {tmdb_name} - {tmdb_id}")
    except IndexError as e:
        logger.error(f"### IndexError ### {e}")
        return 0
    except ConnectionError as e:
        logger.error(e)
        logger.error("### ConnectionError ###")
        return 0

    # save id to cache file
    show_id_cache[showname] = (tmdb_name, tmdb_id)
    save_cache_to_file(show_id_cache, cache_file_path)
    return f"{tmdb_id}"

def search_tv(file, epdata):
    filename = Path(file).name
    ext = Path(file).suffix.strip()
    showname = filename.split(epdata.group(1), 1)[0].replace('.', ' ').strip()
    cleaned_showname = re.sub(r'\(([^)]*)\)', r'\1', showname).replace('-', '').strip()

    episode = epdata.group(0)
    logger.debug(f"searching tv shows for: '{cleaned_showname}' - '{episode}'")

    id = check_show_id(cleaned_showname)
    if id == 0:
        logger.error(f"nothing found on tmdb for '{cleaned_showname}'")
        msg = ["TMDB 404", f"nothing found on tmdb for '{cleaned_showname}'", "not found"]
        ppushitrealgood(msg)
    else:
        logger.debug(f"show id for {cleaned_showname} = {id}")
        try:
            nums = re.search(r"S(\d+)E(\d+)", episode, re.IGNORECASE)
            season_number = nums.group(1)
            episode_number = nums.group(2)
        except AttributeError:
            logger.warning(":( can't parse the thing")

        url = "https://api.themoviedb.org/3/tv/series_id/season/season_number/episode/episode_number"
        url = f"https://api.themoviedb.org/3/tv/{id}/season/{season_number}/episode/{episode_number}"
        headers = {
            "accept": "application/json",
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJjZTI4M2Y4ZmY2OGMwMTk1MzBjNWY1Y2NmMDQ1ZGUyZCIsInN1YiI6IjVhMjVhNTczYzNhMzY4MGI5ZDBkNTU0NyIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.vFgkfokmICq00bnxaVuPxpNbPuC_SonBW_acltEUm5U"
        }

        response = requests.get(url, headers=headers)
        tmdb_data = json.loads(response.text)
        episode_name = tmdb_data['name']
        final_file_name = f"{cleaned_showname} {episode} - {episode_name}{ext}"
        # gotta include /show_name/season/ folders in filename for tv shows
        show_path = f"{cleaned_showname}/Season {season_number}/"
        path_for_tv = f"{show_path}{final_file_name}"
        # os.path.isfile(os.path.join(destination_path, file_name)
        copy_file(file, "tv", path_for_tv)


def process_file(file):
    logger.debug(f"check if media file is a tv show or movie: {file}")
    filename = Path(file).name
    # try 'S##E##-E##' first, then '##x##' - can add more variants as needed
    epdata = re.search(r'(S(\d+)E(\d+)(?:-E(\d{2})|-(\d{2}))?)', filename, re.IGNORECASE)
    if (str(epdata) == "None"):
        epdata = re.search(r'((\d{2})X(\d{2})(?:-E(\d{2})|-(\d{2}))?)', filename, re.IGNORECASE)
    if (str(epdata) == "None"):
        # still no episode data? treat as a movie
        logger.debug("no episode data found, treat as a movie")
        search_movie(file)
    else:
        logger.debug(f"found episode data, treat as tv show: {epdata.group(0)}")
        search_tv(file, epdata)


def check_file(file):
    # logger.debug(f"checking file: {file}")
    ext = Path(file).suffix.strip()
    name = Path(file).name
    media_extensions = {".mp4", ".mkv", ".avi", ".mov", ".wmv"}
    subtitle_extensions = {".srt", ".sub", ".ass", ".vtt"}

    if ext.lower() in media_extensions:
        logger.info(f"process media file: {name}")
        process_file(file)
    elif ext.lower() in subtitle_extensions:
        logger.info(f"process subtitle file: {name}")
        process_file(file)
    else:
        pass
        # logger.debug(f"skip, other file: {name}")

# skip sending messages if there's gonna be a ton of 'em
def check_directory(file_path):
    logger.debug(f"crawling directory: {file_path}")
    for root, dirs, files in os.walk(file_path, topdown=True):
        if "Subs" in dirs:
            # omit Subs folder from processing
            dirs.remove("Subs")
            
        if len(files) > 4:
            msg = ["Heads Up", "Processing " + str(len(files)) + " files from " + str(root.split(os.path.sep)[-2]) + os.path.sep + str(root.split(os.path.sep)[-1]), "new season"]
            logger.debug(str(msg))
            ppushitrealgood(msg)
            global tooManyMessages
            tooManyMessages = True
        
        for name in files:
            # check extensions first
            check_file(name)

def check_file_or_directory(file_path, *args):
    # Process any additional parameters
    for arg in args:
        logger.debug("additional Parameter: %s", arg)

    if "DoNotSort" in args:
        logger.debug("DoNotSort mode: don't actually do anything")
    else:
        logger.debug(f"checking path: {file_path}")
        if os.path.exists(file_path):
            if os.path.isfile(file_path):
                logger.debug(f"{file_path} is a file - check if it's a media file")
                check_file(file_path)
            elif os.path.isdir(file_path):
                logger.debug(f"{file_path} is a directory - loop over dir & look for media files")
                check_directory(file_path)
            else:
                logger.warning(f"{file_path} exists, but its neither a file nor a directory - full stop")
        else:
            logger.error(f"{file_path} does not exist.")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check if the given path is a file or a directory.")
    parser.add_argument("-p", "--path", default="/mnt/torrents/completed", help="The file path to check (default: /mnt/torrents/completed)")
    args, unknown_args = parser.parse_known_args()

    logger = setup_logging()
    check_file_or_directory(args.path, *unknown_args)





# qbt is sending these params
# %N: Torrent name
# %L: Category
# (DoNotSort)

# extras --
# %G: Tags (seperated by comma)
# %F: Content path (same as root path for multifile torrent)
# %R: Root path (first torrent subdirectory path)
# %D: Save path
# %C: Number of files
# %Z: Torrent size (bytes)
# %T: Current tracker
# %I: Info hash


# zj: fucking subtitles...
#    subs will only ever be in a directory structure, either in the passed filepath folder or a subfolder "Subs" or something
#    as long as they're named right, then everything is kosher with the regular process_file function
#    
#   
#   
#   
#   
#   
#   