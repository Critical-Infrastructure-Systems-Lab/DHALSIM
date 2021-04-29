#!/bin/bash

cd ~

git clone git://github.com/mininet/mininet.git

PYTHON=python3 ~/mininet/util/install.sh -fnv

git clone git@gitlab.ewi.tudelft.nl:cse2000-software-project/2020-2021-q4/cluster-06/water-infrastructure/minicps.git

cd minicps

sudo python3 -m pip install -r ~/minicps/requirements-dev.txt

sudo python3 -m pip install .

cd ~
