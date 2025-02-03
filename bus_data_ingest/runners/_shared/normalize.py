#!/usr/bin/env python3

import calendar
import datetime
import pytz
import json
import logging
import os
import pathlib
import re
import sys
import urllib.parse
from typing import List

import yaml
import campuspulse_bus_ingest_schema as schema
from dateutil import parser as dateparser
from bus_data_ingest.utils.jsonserial import json_serial

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(name)s:%(message)s",
    datefmt="%m/%d/%Y %H:%M:%S",
)
logger = logging.getLogger("_shared/parse.py")

OUTPUT_DIR = pathlib.Path(sys.argv[1])
INPUT_DIR = pathlib.Path(sys.argv[2])
YML_CONFIG = pathlib.Path(sys.argv[3])


def _get_config(yml_config: pathlib.Path) -> dict:
    with open(yml_config, "r") as stream:
        try:
            config = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    return config


# def _get_source(config: dict, site: dict, timestamp: str) -> schema.EventSource:
#     return schema.EventSource(
#         source_id=site["UID"],
#         processed_at=timestamp,
#         # data=site,
#     )


# def _get_inventory(site: dict) -> List[schema.Vaccine]:
#     vaccines = site["vaccines"]

#     inventory = []

#     pfizer = re.search("pfizer", vaccines, re.IGNORECASE)
#     moderna = re.search("moderna", vaccines, re.IGNORECASE)
#     johnson = re.search("janssen", vaccines, re.IGNORECASE) or re.search(
#         "johnson", vaccines, re.IGNORECASE
#     )

#     # some clinics specified all 3 vaccines but stated that they'll be given based on what's available.
#     if pfizer:
#         inventory.append(schema.Vaccine(vaccine="pfizer_biontech"))
#     if moderna:
#         inventory.append(schema.Vaccine(vaccine="moderna"))
#     if johnson:
#         inventory.append(schema.Vaccine(vaccine="johnson_johnson_janssen"))

#     if len(inventory) == 0:
#         return None

#     return inventory


# def _get_address(site: dict) -> schema.Address:
#     address = site["address"]
#     address_split = address.split(", ")

#     adr2 = None if len(address_split) == 3 else address_split[1]

#     return schema.Address(
#         street1=address_split[0],
#         street2=adr2,
#         city=address_split[-2].replace(f" {config['state'].upper()}", ""),
#         state=config["state"].upper(),
#         zip=address_split[-1],
#     )


# def _get_notes(site: dict) -> List[str]:
#     return [site["info"], site["special"]]


# def _get_opening_dates(site: dict) -> List[schema.OpenDate]:
#     date = site["date"]
#     date_split = date.split("/")

#     return [
#         schema.OpenDate(
#             opens=f"{date_split[2]}-{date_split[0]}-{date_split[1]}",
#             closes=f"{date_split[2]}-{date_split[0]}-{date_split[1]}",
#         )
#     ]


# def _get_opening_hours(site: dict) -> List[schema.OpenHour]:
#     date = site["date"]
#     time = site["hours"]

#     time_split = time.split(" - ")

#     date_dt = datetime.datetime.strptime(date, "%m/%d/%Y")
#     time_start = datetime.datetime.strptime(time_split[0], "%I:%M %p")
#     time_end = datetime.datetime.strptime(time_split[1], "%I:%M %p")

#     return [
#         schema.OpenHour(
#             day=calendar.day_name[date_dt.weekday()].lower(),
#             opens=time_start.strftime("%H:%M"),
#             closes=time_end.strftime("%H:%M"),
#         )
#     ]


# def _get_contact(config: dict, site: dict) -> List[schema.Contact]:
#     return [
#         schema.Contact(
#             contact_type="booking",
#             website=f"{config['url']}/appointment/en/client/registration?clinic_id={site['clinic_id']}",
#         )
#     ]


def _parse_location(site):
    try:
        loc = site["LOCATION"]
    except Exception as e: 
        logger.info("Skipping parsing for one record due to exception")
        logger.warning(
            "An error occurred while parsing the address for record "
            + site["UID"]
            + ": "
            + str(e)
        )
        return None

    return schema.Location(
        street=loc,
        # city= city,
        # state=state
    )


def _parse_time(site, key, nullable=False, defaulttz=None):
    
    should_ignore_tz = defaulttz is None

    parsed_date = dateparser.parse(site.get(key), ignoretz=should_ignore_tz) if site.get(key) else None

    if nullable and parsed_date is None:
        return None
    
    needs_tz = parsed_date.tzinfo is None

    if needs_tz:
        parsed_date = parsed_date.replace(tzinfo=defaulttz)

    return parsed_date 

def _get_out_filepath(in_filepath: pathlib.Path, out_dir: pathlib.Path) -> pathlib.Path:
    filename, _ = os.path.splitext(in_filepath.name)
    return out_dir.joinpath(f"{filename}.normalized.ndjson")


def _normalize_stops(stops: dict) -> List[schema.Stop]:
    return [schema.Stop(
        stop_id = site["stop_id"],
        name = site["name"],
        times = _normalize_times(site["times"])
    ) for site in stops]

def _normalize_times(times: list[dict]) -> List[schema.Stop]:
    return [schema.Time(**t) for t in times ]


def normalize(config: dict, stops: dict, timestamp: str) -> str:
    # group = config["state"] 
    # source = config["site"]
    # ident = config["source_url"].split("/")[-1]
    # return schema.BusSchedule(
    #     identifier = f"{group}_{source}_{ident}",#: str
    #     source_url = config["source_url"],
    #     # service_alerts = _normalize_service_alerts(site),
    #     routes = 
    return schema.Route(
            route_id = config["route_id"],
            name = config["route_name"],
            stops = _normalize_stops(stops),
            source_url = config["source_url"]
        )#,
    # )


parsed_at_timestamp = datetime.datetime.utcnow().isoformat()

config = _get_config(YML_CONFIG)

if config["parser"] == "table":
    for input_file in INPUT_DIR.glob("*.ndjson"):
        output_file = _get_out_filepath(input_file, OUTPUT_DIR)
        with input_file.open() as parsed_lines:
            with output_file.open("w") as fout:
                lines = [json.loads(line) for line in parsed_lines]
                    # site = 
                normalized_site = normalize(config, lines, parsed_at_timestamp)
                json.dump(normalized_site.dict(exclude_unset=True), fout, default=json_serial)
                fout.write("\n")
