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

# TODO
# multi-part episodes
# overwrite mode

def setup_logging():
    log_file = "/var/log/zort.log"
    if "log_level" in settings:
        # print("using log level from settings")
        log_level = settings['log_level']
    else:
        # print("using default DEBUG log level")
        log_level = logging.DEBUG
    
    logging.basicConfig(
        level=log_level,
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

def load_settings():
    settings_file_path = "/home/pi/piscripts/brand_new_sort_settings.json"
    settings = load_from_file(settings_file_path)
    # print(f"\n$$$ settings loaded $$$\n")
    global media_extensions
    global subtitle_extensions
    media_extensions = settings["media_extensions"]
    subtitle_extensions = settings["subtitle_extensions"]
    # for n in settings:
    #     print(f"\t*** item:: '{n}' | {settings[n]}")
    return settings

tooManyMessages = False

# simplepush notifications
def ppushitrealgood(msg):
    global tooManyMessages
    logger.debug(f"tooManyMessages = {tooManyMessages}")
    sp_key = settings["simplepush_key"]
    sp_url = "https://api.simplepush.io/send"
    if not tooManyMessages:
        try:
            # assemble message parameters
            msg_title = msg[0]
            msg_body = msg[1]
            msg_event = msg[2]
            msgdata = parse.urlencode({'key': sp_key, 'title': f'{msg_title}', 'msg': f'{msg_body}', 'event': f'{msg_event}'}).encode()
            req = request.Request(sp_url, data=msgdata)
            response = request.urlopen(req)
            logger.debug(f"response={response}")
        except IndexError as e:
            logger.error({e})
            logger.error(f"error sending message: {msg}")

# save searched ids to cut down on api calls
def save_to_file(cache_dict, file_path):
    with open(file_path, "w") as file:
        json.dump(cache_dict, file)
def load_from_file(file_path):
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


def copy_file(file, type, file_name, message_body):
    # fix source path for copy
    source_path = args.path
    if args.path.startswith("cp/"): # helpful alias for the cp mapping
        source_path = f"/mnt/torrents/completed/{args.path[3:]}"
    if not os.path.isfile(f'{source_path}'):
        # directory-torrents need the media filename appended back
        source_path += f"/{Path(file).name}"
    logger.debug(f"source_path = '{source_path}' -- isfile:{os.path.isfile(f'{source_path}')} -- exists: {os.path.exists(f'{source_path}')}")

    # set destination path
    destination_path = ""
    item_label = ""
    if type == "tv":
        # include show & season folders
        destination_path = f"/mnt/tv/{file_name}"
        item_label = "New Episode"
    elif type == "movie":
        destination_path = f"/mnt/movies/{file_name}"
        item_label = "New Movie"
    logger.debug(f"destination_path = '{destination_path}' -- exists:{os.path.exists(f'{destination_path}')}")
    
    # sanity check & copy file
    logger.debug("$$$ os.path.isfile(f'{source_path}') = " + str(os.path.isfile(f'{source_path}')))
    logger.debug("$$$ os.path.exists(f'{source_path}') = " + str(os.path.exists(f'{source_path}')))
    logger.debug("$$$ os.path.exists(f'{destination_path}') = " + str(os.path.exists(f'{destination_path}')))
    
    if os.path.exists(f'{destination_path}'):
        if args.overwrite:
            try:
                output = shutil.copy2(source_path, destination_path)
                msg = [f"{os.path.basename(file_name).rsplit('.', 1)[0]}" + " (overwrite)", f"{message_body}", "overwrite"]
                logger.info(f"{msg[1]}")
            except FileExistsError as e:
                logger.error(e)
                logger.error(":/")
                msg = ["ERROR", f"error trying to copy '{source_path}' to '{destination_path}", "file error"]
            finally:
                logger.debug(f"copy result:: '{output}'")
        else:
            logger.warning(f"file already exists in destination: {destination_path}")
            msg = ["duplicate media", f"You already have {file}", "duplicate"]
    else:
        if os.path.isfile(f'{source_path}') and os.path.exists(f'{source_path}'):
            try:
                os.makedirs(os.path.dirname(f'{destination_path}'), exist_ok=True)
                logger.debug(f"shutil.copy('{source_path}', '{destination_path}')")
                output = shutil.copy(f'{source_path}', f'{destination_path}')
                msg = [f"{os.path.basename(file_name).rsplit('.', 1)[0]}", f"{message_body}", f"{item_label}"]
                logger.info(f"{msg[1]}")
            except FileExistsError as e:
                logger.error(e)
                logger.error(":/")
                msg = ["ERROR", f"error trying to copy '{source_path}' to '{destination_path}", "file error"]
            finally:
                logger.debug(f"copy result:: '{output}'")
        

    # send simplepush notification (omit entirely for subtitle files)
    ext = os.path.splitext(Path(file).name)[1]
    global subtitle_extensions
    if ext not in subtitle_extensions:
        logger.debug(f"not a subtitle file, proceed normally: {ext}")
        ppushitrealgood(msg)
    else:
        logger.debug(f"no messaging for subtitle files: {ext}")

def get_tmdb_headers():
    logger.debug(f"\n&&&settings['tmdb_bearer_token'] = {settings['tmdb_bearer_token']}\n")
    return {
        "accept": "application/json",
        "Authorization": f"Bearer {settings['tmdb_bearer_token']}"
    }

def search_movie(file):
    filename = Path(file).name
    ext = Path(file).suffix.strip()
    logger.debug(f"search movies for: {filename}")

    try:
        yr = re.search(r'[\(|\[|" "|\.](\d{4})[\)|\]|" "|\.]', filename, re.IGNORECASE)
        title = filename.split(yr.group(0), 1)[0].strip().replace(".", " ")
        year = yr.group(1)
        logger.debug(f"movie: {title} ({year})")

        headers = get_tmdb_headers()

        if args.id:
            # do the force id
            logger.debug(f"forcing use of tmdb id {args.id}")
            url = f"https://api.themoviedb.org/3/movie/{args.id}"
            params = {}
        else:
            url = "https://api.themoviedb.org/3/search/movie"
            params = {
                "query": title, 
                "year": year
            }
        
        response = requests.get(url, headers=headers, params=params)
        jsonlist = json.loads(response.text)
        
        if args.id:
            tmdb_name = jsonlist['title']
            year = jsonlist['release_date'][:4]
            final_file_name = f"{tmdb_name} ({year}){ext}"
            message_body = f"{jsonlist['overview']}"
        else:
            if int(jsonlist['total_results']) == 0:
                if ext.lower() not in subtitle_extensions:
                    msg = ["TMDB 404", f"nothing found on tmdb for '{title} ({year})'", "not found"]
                    logger.warning(f"{msg[1]}")
                    ppushitrealgood(msg)
            else:
                tmdb_name = jsonlist['results'][0]['title']
                year = jsonlist['results'][0]['release_date'][:4]
                final_file_name = f"{tmdb_name} ({year}){ext}"
                message_body = f"{jsonlist['results'][0]['overview']}"

        logger.debug(f"final file name: '{final_file_name}'")
        # assemble message for notification
        copy_file(file, "movie", final_file_name, message_body)
    except AttributeError as e:
        logger.warning(f"can't parse movie name/year for: {filename}")
        logger.error(e)
    except IndexError as e:
        logger.warning(f"something missing from jsonlist\n{jsonlist}")
        logger.error(e)
    except KeyError as e:
        logger.warning(f"given force-id appears to be invalid - {jsonlist['status_message']}")


def check_show_id(showname):
    cache_file_path = "/home/pi/piscripts/show_id_cache.json"
    global show_id_cache
    show_id_cache = load_from_file(cache_file_path)

    # for n in show_id_cache:
    #     logger.debug(f"\t*** showname:: '{n}' | {show_id_cache[n]}")
         
    if showname in show_id_cache:
        # return id saved locally
        logger.debug(f"returning local id: {show_id_cache[showname][1]}")
        return f"{show_id_cache[showname][1]}"
    else:
        logger.debug(f"can't find '{showname}' in cache, lookup on tmdb")

    # otherwise lookup show id from tmdb & save it
    url = "https://api.themoviedb.org/3/search/tv"

    headers = get_tmdb_headers()
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
    save_to_file(show_id_cache, cache_file_path)
    return f"{tmdb_id}"

def search_tv(file, epdata):
    filename = Path(file).name
    ext = Path(file).suffix.strip()
    showname = filename.split(epdata.group(1), 1)[0].replace('.', ' ').strip()
    cleaned_showname = re.sub(r'\(([^)]*)\)', r'\1', showname).replace('-', '').strip()

    episode = epdata.group(0)
    logger.debug(f"searching tv shows for: '{cleaned_showname}' - '{episode}'")

    id = check_show_id(cleaned_showname)
    # for n in show_id_cache:
    #     print(f"\t^^^ show_id_cache[{n}] = {show_id_cache[n]}")
    final_show_name = show_id_cache[cleaned_showname][0]
    if id == 0:
        logger.error(f"nothing found on tmdb for '{cleaned_showname}'")
        msg = ["TMDB 404", f"nothing found on tmdb for '{cleaned_showname}'", "not found"]
        ppushitrealgood(msg)
    else:
        logger.debug(f"show id for {cleaned_showname} = {id} ({final_show_name})")
        try:
            nums = re.search(r"S(\d+)E(\d+)", episode, re.IGNORECASE)
            season_number = nums.group(1)
            episode_number = nums.group(2)
        except AttributeError:
            logger.warning(f"can't parse epdata: '{episode}'")
            

        # season number offsetting
        season_offsets = settings.get("season_offset", [])
        if id in season_offsets:
            index = season_offsets.index(id)
            offset_value = season_offsets[index + 1] if index < len(season_offsets) - 1 else None
            season_number = int(season_number) + int(offset_value)
            logger.warning(f"offsetting season number for {final_show_name} by {offset_value} to {season_number}")

        url = f"https://api.themoviedb.org/3/tv/{id}/season/{season_number}/episode/{episode_number}"
        headers = get_tmdb_headers()

        response = requests.get(url, headers=headers)
        tmdb_data = json.loads(response.text)
        
        if 'success' in tmdb_data and not tmdb_data['success']:
            msg = ["404", f"{tmdb_data['status_message']} {showname} {episode}", "404"]
            logger.error(f"Error: {msg[1]}")
            ppushitrealgood(msg)
        else:
            episode_name = tmdb_data['name']
            final_file_name = f"{final_show_name} {episode} - {episode_name}{ext}"
            # gotta include /show_name/season/ folders in filename for tv shows
            show_path = f"{final_show_name}/Season {season_number}/"
            path_for_tv = f"{show_path}{final_file_name}"
            message_body = f"{tmdb_data['overview']}"
            copy_file(file, "tv", path_for_tv, message_body)


def process_file(file):
    logger.debug(f"check if media file is a tv show or movie: {file}")
    filename = Path(file).name
    # try 'S##E##-E##' first, then '##x##' - can add more variants as needed
    epdata = re.search(r'(S(\d+)E(\d+)(?:-E(\d{2})|-(\d{2}))?)', filename, re.IGNORECASE)

    if (str(epdata) == "None"):
        epdata = re.search(r'((\d{2})X(\d{2})(?:-E(\d{2})|-(\d{2}))?)', filename, re.IGNORECASE)
        if "daily.show" in filename.lower():
            logger.debug("$$ FOUND THE DAILY SHOW!!!")
            epdata = re.search(r'(\d{4}\.\d{2}\.\d{2})', filename)

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
    global media_extensions
    global subtitle_extensions

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
    parser = argparse.ArgumentParser(description="Media sorting script")
    parser.add_argument("-p", "--path", default="/mnt/torrents/completed/nothing", help="The file path to check (defaults to '/mnt/torrents/completed/nothing' for safety)")
    parser.add_argument("-i", "--id", help="force a movie (ONLY a movie) to use the specified tmdb id")
    parser.add_argument("-o", "--overwrite", action="store_true", help="overwrite mode, replaces an existing file")

    args, unknown_args = parser.parse_known_args()
    
    # try to load settings file
    settings = load_settings()
    
    logger = setup_logging()
    
    # save id to cache file
    settings_file_path = "/home/pi/piscripts/brand_new_sort_settings.json"
    
    # save_to_file(settings, settings_file_path)
    
    # do the thing
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