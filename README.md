# ptyme-track
Time tracking based on file modifications and signed reporting. The P is silent like in Pterodactyl

## Usage

### Server / client
Simply run the server with `ptyme_track --server`

For the client, use ptyme_track --client

### Running locally
Simply run `ptyme_track` in the background.

### Setting directories to watch
By default, the current working directory is used and hidden directories are ignored. To manually set paths, use the `PTYME_WATCHED_DIRS` environment variable.

## Cementing work

To cement your time record, use `ptyme_track --cement <name>`. It is recommended name is your github name. Note this is a filename so it needs to be filename safe (and unique from others).
