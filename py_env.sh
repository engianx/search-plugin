#!/bin/bash

# Add src to PYTHONPATH, relative to the script's location, don't use pwd
DIR="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"

# If src is not in PYTHONPATH, add it
if [[ ":$PYTHONPATH:" != *":$DIR/src:"* ]]; then
    export PYTHONPATH="$DIR/src:$PYTHONPATH"
fi

source .venv/bin/activate
