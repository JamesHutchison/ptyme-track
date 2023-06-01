import os
import uuid

### client concerns ###
PTYME_TRACK_DIR = os.environ.get("PTYME_TRACK_DIR", ".ptyme_track")
# colon seperated dirs
PTYME_WATCHED_DIRS = os.environ.get("PTYME_WATCHED_DIRS", ".")
PTYME_IGNORED_DIRS = os.environ.get("PTYME_IGNORED_DIRS", "node_modules:__pycache__")
PTYME_WATCH_INTERVAL_MIN = int(os.environ.get("PTYME_WATCH_INTERVAL_MIN", "2"))
######

### server concerns ###
SERVER_ID = os.environ.get("PTYME_SERVER_ID", str(uuid.uuid4()))
SECRET_PATH = os.environ.get("PTYME_SECRET_PATH", ".ptyme.secret")
# SECRET is used if SECRET_PATH does not exist
SECRET = os.environ.get("PTYME_SERVER_SECRET", str(uuid.uuid4()))
#######

### used by both client and server ###
SERVER_URL = os.environ.get("PTYME_SERVER_URL", "http://localhost:8941")

### git ci diff ###
PTYME_TRACK_BASE_BRANCH = os.environ.get("PTYME_TRACK_BASE_BRANCH")
PTYME_TRACK_FEATURE_BRANCH = os.environ.get("PTYME_TRACK_FEATURE_BRANCH")
#######
