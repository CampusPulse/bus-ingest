#!/usr/bin/env python3

#
# Parse stage should convert raw data into json records and store as ndjson.
#

import json
import pathlib
import sys

input_dir = pathlib.Path(sys.argv[2])
input_file = input_dir / "data.json"
output_dir = pathlib.Path(sys.argv[1])
output_file = output_dir / "data.parsed.ndjson"

with input_file.open() as fh:
    raw_json = json.load(fh)

with output_file.open("w") as fout:
    # for feature in raw_json["features"]:
    json.dump(raw_json, fout)
    fout.write("\n")
