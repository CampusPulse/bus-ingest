#!/usr/bin/env bash

#
# Fetch stage should retrieve raw data from external source and store it unmodified
#

set -Eeuo pipefail

output_dir=""

if [ -n "${1}" ]; then
    output_dir="${1}"
else
    echo "Must pass an output_dir as first argument"
fi

### Replace the following with your implementation ###

echo "Fetching into ${output_dir}"

###

(cd "$output_dir" && curl --silent "https://www.rit.edu/parking/2-campus-connection-shuttle" -o 'schedule.html')
