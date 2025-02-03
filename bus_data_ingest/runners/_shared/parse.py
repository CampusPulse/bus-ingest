#!/usr/bin/env python3

#
# Parse stage should convert raw data into json records and store as ndjson.
#

import json
from json import JSONEncoder
import datetime
import os
import pathlib
import re
import sys
from typing import Dict, List
from datetime import datetime
from pathlib import Path

import yaml
from bs4 import BeautifulSoup

from bus_data_ingest.utils.log import getLogger

logger = getLogger(__file__)

OUTPUT_DIR = pathlib.Path(sys.argv[1])
INPUT_DIR = pathlib.Path(sys.argv[2])
YML_CONFIG = pathlib.Path(sys.argv[3])



def soupify_file(input_path: pathlib.Path) -> List[BeautifulSoup]:
    """Opens up a provided file path, feeds it into BeautifulSoup.
    Returns a new BeautifulSoup object for each found table
    """
    with open(input_path, "r") as fd:
        return BeautifulSoup(fd, "html.parser")


def extract_room_info(page: BeautifulSoup) -> Dict[str, str]:
    """Takes a BeautifulSoup tag corresponding to a page as input,
    Returns a dict of labeled data, suitable for transformation into ndjson
    """
    result: Dict[str, str] = {}


    roomSizes = page.find_all("div",class_="field--name-field-room-size")
    singleSemCosts = page.find_all("div",class_="field--name-field-per-semester-per-person")
    twoSemCosts = page.find_all("div",class_="field--name-field-per-2-semesters-per-person")
    roomSizeArr = []
    singSemCostArr = []
    twoSemCostArr = []
    for roomSize in roomSizes:
        roomSizeArr.append(roomSize.text)
    for singleSemCost in singleSemCosts:
        singSemCostArr.append(singleSemCost.text)
    for twoSemCost in twoSemCosts:
        twoSemCostArr.append(twoSemCost.text)

    result["rooms"] = []

    for i in range(len(roomSizeArr)):
        roomStyle = {}
        roomStyle["size"] = roomSizeArr[i]
        roomStyle["cost"] = {
            "semster": singSemCostArr[i],
            "year": twoSemCostArr[i],
            "summer":""
        }
        result["rooms"].append(roomStyle)

    return result

def _enforce_keys(config: dict, keys: List[str]) -> None:
    for key in keys:
        if key not in config:
            logger.error("config file must have key 'state'. This config does not.")
            raise KeyError(f"{key} not found")


def _get_config(yml_config: pathlib.Path) -> dict:
    with open(yml_config, "r") as stream:
        try:
            config = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            logger.error(exc)

    _enforce_keys(config, ["state", "site", "parser"])

    return config


def _get_out_filepath(in_filepath: pathlib.Path, out_dir: pathlib.Path) -> pathlib.Path:
    filename, _ = os.path.splitext(in_filepath.name)
    return out_dir.joinpath(f"{filename}.parsed.ndjson")


def _log_activity(
    state: str, site: str, in_filepath: pathlib.Path, out_filepath: pathlib.Path
) -> None:
    logger.info(
        "(%s/%s) parsing %s => %s",
        str(state).upper(),
        str(site).lower(),
        in_filepath,
        out_filepath,
    )


def _output_ndjson(json_list: List[dict], out_filepath: pathlib.Path, dump_cls=None) -> None:
    with out_filepath.open("w") as fout:
        for obj in json_list:
            if dump_cls is not None:
                json.dump(obj, fout, cls=dump_cls)
            else:
                json.dump(obj, fout)

            fout.write("\n")


# def _prepmod_find_data_item(parent, label, offset):
#     row_matches = [x for x in parent.find_all(["p", "div"]) if label in x.get_text()]
#     try:
#         content = row_matches[-1].contents[offset]
#     except IndexError:
#         return ""
#     return content.strip() if isinstance(content, str) else content.get_text().strip()

def _process_stop_name(name: str) -> str:
    if name.startswith("Gleason Circle"):
        return "Gleason Circle"
    else:
        return name

def _get_stop_id(name: str, mapping) -> str:
    name = _process_stop_name(name)
    if mapping.get(name):
        return mapping[name]
    else:
        return name


def _dedup_dicts(input_dicts, key) -> dict:
    """ deduplicate a dict using its value at the given key"""
    output_dict = []
    seen = set()
    for k in input_dicts:
        if k[key] not in seen:
            seen.add(k[key])
            output_dict.append(k)
    return output_dict

config = _get_config(YML_CONFIG)
# EXTRACT_CLINIC_ID = re.compile(r".*clinic(\d*)\.png")

if config["parser"] == "table":
    """
    parse schedule table into json data
    """

    busstops = INPUT_DIR.joinpath("busstops.json")
    # parse busstops.json with Pathli
    busstops = json.loads(busstops.read_text())

    stops = busstops["stops"]
    # create mapping from stop name to stop id
    stop_id_map = {stop["name"]: stop["id"] for stop in stops}


    for schedule in INPUT_DIR.glob("**/*.html"):
        if not schedule.is_file():
            continue

        soup = soupify_file(schedule)
        table = soup.find('table')

        if not table:
            print(f"No table found in {schedule}")
            continue
        
        headers = [th.get_text(strip=True) for th in table.find_all('th')]
        # run through get_stop_id and dedup to condense gleason circle stuff
        # headers = [_process_stop_name(k) for k in headers]
        # # remove duplicates in the headers, preserving order
        # headers = list(dict.fromkeys(headers))
        
        scheduledata = {}
        
        for row in table.find_all('tr')[1:]:  # Skip header row
            cells = row.find_all('td')
            for i, cell in enumerate(cells):
                if i < len(headers):
                    name = headers[i]
                    if name not in scheduledata:
                        scheduledata[name] = []
                    
                    scheduledata[name].append(datetime.strptime(cell.get_text(strip=True), "%I:%M %p").strftime("%H:%M"))

        # turn each key of scheduledata into a dict
        data = []
        for name, times in scheduledata.items():
            data.append({
                "name": _process_stop_name(name),
                "stop_id": _get_stop_id(name, stop_id_map),
                "times": times
            })

        # deduplicate by stop_id where the values contain lists
        data = _dedup_dicts(data, "stop_id")

        out_filepath = _get_out_filepath(schedule, OUTPUT_DIR)

        _log_activity(config["state"], config["site"], schedule, out_filepath)

        _output_ndjson(data, out_filepath)

elif config["parser"] == "passthrough":
    """
    Parse files containing lists of json objects.
    """
    json_filepaths = INPUT_DIR.glob("*.json")
    for in_filepath in json_filepaths:
        with in_filepath.open() as fin:
            json_list = json.load(fin)

        out_filepath = _get_out_filepath(in_filepath, OUTPUT_DIR)
        _log_activity(config["state"], config["site"], in_filepath, out_filepath)

        _output_ndjson(json_list, out_filepath)

# elif config["parser"] == "prepmod":
#     """
#     Parse HTML 'prepmod' data.
#     """
#     input_filenames = INPUT_DIR.glob("*.html")

#     for filename in input_filenames:
#         out_filepath = _get_out_filepath(filename, OUTPUT_DIR)
#         text = open(filename, "r").read()
#         soup = BeautifulSoup(text, "html.parser")

#         # classes only used on titles for search results
#         with open(out_filepath, "w") as fout:
#             for title in soup.select(".text-xl.font-black"):
#                 parent = title.parent
#                 combined_name = title.get_text().strip()
#                 name, date = combined_name.rsplit(" on ", 1)
#                 address = title.find_next_sibling("p").get_text().strip()
#                 vaccines = _prepmod_find_data_item(parent, "Vaccinations offered", -2)
#                 ages = _prepmod_find_data_item(parent, "Age groups served", -1)
#                 additional_info = _prepmod_find_data_item(
#                     parent, "Additional Information", -1
#                 )
#                 hours = _prepmod_find_data_item(parent, "Clinic Hours", -1)
#                 available_count = (
#                     _prepmod_find_data_item(parent, "Available Appointments", -1) or 0
#                 )
#                 special = _prepmod_find_data_item(parent, "Special Instructions", -1)
#                 if content := parent.find_next_sibling("div", "map-image").find("img"):
#                     find_clinic_id = EXTRACT_CLINIC_ID.match(content["src"])
#                     clinic_id = find_clinic_id.group(1)
#                 else:
#                     clinic_id = ""
#                 data = {
#                     "name": name,
#                     "date": date,
#                     "address": address,
#                     "vaccines": vaccines,
#                     "ages": ages,
#                     "info": additional_info,
#                     "hours": hours,
#                     "available": available_count,
#                     "special": special,
#                     "clinic_id": clinic_id,
#                 }
#                 json.dump(data, fout)
#                 fout.write("\n")
else:
    logger.error("Parser '%s' was not recognized.", config["parser"])
    raise NotImplementedError(f"No shared parser available for '{config['parser']}'.")
