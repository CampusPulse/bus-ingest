#!/usr/bin/env python3

#
# Parse stage should convert raw data into json records and store as ndjson.
#

import json
import pathlib
import sys
import gtfs_kit as gk


input_dir = pathlib.Path(sys.argv[2])
input_file = input_dir / "gtfs.zip"
output_dir = pathlib.Path(sys.argv[1])
output_file = output_dir / "data.parsed.ndjson"

#Read the feed with gtfs-kit
feed = (gk.read_feed(input_dir, dist_units='mi'))

#Search for errors and warnings in the feed
print(feed)

# with output_file.open("w") as fout:
#     for feature in raw_json["features"]:
#         json.dump(feature, fout)
#         fout.write("\n")
