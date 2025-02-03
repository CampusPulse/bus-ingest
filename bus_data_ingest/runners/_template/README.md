# Example Site

To start a pipeline for a new site, start by copying from the files in this directory.

some of the files have duplicate information to provide examples of different ways to do it (i.e. parsing html into ndjson vs parsing json into ndjson).

Each runner only needs one fetch, one parse, and one normalize file in its folder (can be any relevant file extension such as `.sh` or `.py`). They must be named `fetch`, `parse`, and `normalize` and be marked as executable though.


`.yml` files can be an option for offloading lots of near-identical fetch, parse, or normalize jobs to shared runners, but this was mostly used for ArcGIS parsing in the older VaccinateTheStates version of this pipeline and is mostly unused 
