# Ptyme Track
The obnoxiously hard to spell time tracking based on file modifications and signed time reporting. The P is silent like in Pterodactyl

## Usage

### Server / client
Simply run the server with `ptyme_track --server`

For the client, use ptyme_track --client

### Running locally
Simply run `ptyme_track --standalone` in the background.

### Setting directories to watch
By default, the current working directory is used and hidden directories are ignored. To manually set paths, use the `PTYME_WATCHED_DIRS` environment variable.

## Cementing work
To cement your time record, use `ptyme_track --cement <name>`. It is recommended name is your github name. Note this is a filename so it needs to be filename safe (and unique from others). This will create a file `.ptyme_track/<name>`


## Getting a time summary
To get a time summary enter the path to the file. For example, `ptyme_track --time-blocks .ptyme_track/JamesHutchison` will give you a summary of the time blocks for JamesHutchison.

```
...
{"start": "2023-05-30 19:00:34", "end": "2023-05-30 19:10:34", "duration": "0:10:00"}
{"start": "2023-05-31 04:02:31", "end": "2023-05-31 04:20:31", "duration": "0:18:00"}
{"start": "2023-05-31 04:20:31", "end": "2023-05-31 04:32:32", "duration": "0:12:01"}
{"start": "2023-05-31 04:30:32", "end": "2023-05-31 04:40:32", "duration": "0:10:00"}
{"start": "2023-05-31 04:56:33", "end": "2023-05-31 05:08:33", "duration": "0:12:00"}
{"start": "2023-05-31 05:03:51", "end": "2023-05-31 05:17:50", "duration": "0:13:59"}
Total duration:  11:47:22
```

## Adding to the CI

Add this workflow:

```yaml
name: Get logged time
on:
  pull_request:
    paths:
      - '.ptyme_track/*'

jobs:
  track-time:
    uses: JamesHutchison/ptyme-track/.github/workflows/time_tracking.yaml
    permissions:
      pull-requests: write
    with:
      base-branch: origin/${{ github.event.pull_request.base.ref }}
      pr-number: ${{ github.event.pull_request.number }}
```
