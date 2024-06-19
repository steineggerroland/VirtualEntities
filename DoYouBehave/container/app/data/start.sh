#!/bin/bash

cd "$(dirname "$0")/../../behave" || exit

if [ ! -f main.py ]; then
    echo "Error: main.py does not exist."
    exit 1
fi

pip install -r requirements.txt || echo "Failed to install requirements"
python3 -d main.py /behave_runtime/test-config/config.yaml /behave_runtime/test-data/db.json /behave_runtime/test-data/default.log || echo "Failed to run behave"
