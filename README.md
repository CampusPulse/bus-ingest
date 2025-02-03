# bus-data-ingest

<!-- [![see results in vaccine-feed-ingest-results](https://img.shields.io/static/v1?label=see%20results&message=vaccine-feed-ingest-results&color=brightgreen)](https://github.com/CAVaccineInventory/vaccine-feed-ingest-results) -->

Pipeline for ingesting data about events on campus. 
## Contributing

### How to

1. Configure your environment ([instructions on the wiki](https://github.com/CampusPulse/data-ingest/wiki/Development-environment-setup)).
1. Choose an unassigned [issue](https://github.com/CampusPulse/data-ingest/issues), and comment that you're working on it.
1. Open a PR containing a new `fetch`, `parse`, or `normalize` script! ([details on these stages](https://github.com/CampusPulse/data-ingest/wiki/Runner-Pipeline-Stages))

<!-- Results are periodically committed to [`vaccine-feed-ingest-results`](https://github.com/CAVaccineInventory/vaccine-feed-ingest-results). Once your PR is merged, you will be able to see the output of your work there! -->

### Run the tool

[See the wiki](https://github.com/CampusPulse/data-ingest/wiki/Run-bus-data-ingest) for instructions on how to run `bus-data-ingest`.


## Production Details

For more information on ([pipeline stages](https://github.com/CampusPulse/data-ingest/wiki/Runner-Pipeline-Stages)) and how to contribute, [see the wiki](https://github.com/CampusPulse/data-ingest/wiki)!

The below details on interacting with our production environment are intended for staff developers.
### Overall setup

In production, all stages for all runners are run, and outputs are stored to the `vaccine-feeds` bucket on GCS.

If you are developing a feature that interacts with the remote storage, you need to test GCS then install the `gcloud` SDK from setup instructions and use the `vaccine-feeds-dev` bucket (you will need to be granted access).

Results are also periodically committed to [`vaccine-feed-ingest-results`](https://github.com/CAVaccineInventory/vaccine-feed-ingest-results).

### Loading to a frontend API

To load the generated output to a frontend API, the following bash one-liner can be used to grab the most recent normalized output from all runner stages and concatenate them together into one file.

`find out -type f -mtime -1 -exec ls -lt {} + | grep "normalized" | awk '{print $NF}' 2> /dev/null |xargs cat > "$(date +'%Y-%m-%d')_concatenated_events.parsed.normalized.ndjson"`



<!-- 1. Authenticate to gcloud with an account that has access to `vaccine-feeds-dev` bucket.

  ```sh
  gcloud auth application-default login
  ```

1. Run ingestion with an GCS `--output-dir`

  ```sh
  poetry run bus-data-ingest all-stages --output-dir=gs://vaccine-feeds-dev/locations/
  ```

### Load Source Locations

#### VIAL Setup

1. Request an account on the VIAL staging server `https://vial-staging.calltheshots.us`

1. Create an API Key for yourself at `https://vial-staging.calltheshots.us/admin/api/apikey/`

1. Store the API key in project `.env` file with the var `VIAL_APIKEY`

#### Load Usage

- Load SF.GOV source feed to VIAL

  ```sh
  poetry run bus-data-ingest load-to-vial ca/sf_gov
  ``` -->
