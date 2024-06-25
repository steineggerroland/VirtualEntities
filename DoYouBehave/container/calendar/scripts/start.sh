#!/bin/bash
useradd -ms /bin/bash radicale
sudo su radicale
cd /home/radicale || return
mkdir /home/radicale/radicale-data
pip install --upgrade radicale
radicale --storage-filesystem-folder=/home/radicale-data --config=/radicale-config/config
