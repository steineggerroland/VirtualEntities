#!/bin/bash

cd "$(dirname "$0")/.." || exit

if [ ! -f main.py ]; then
    echo "Error: main.py does not exist."
    exit 1
fi

pip install -r requirements.txt || echo "Failed to install requirements"
python3 main.py /behave/test-config/config.yaml /behave/test-data/config.json || echo "Failed to run behave"
