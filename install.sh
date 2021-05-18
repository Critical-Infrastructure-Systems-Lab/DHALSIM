#!/bin/bash

cd ~

sudo apt update

## Installing necessary packages
sudo apt install git

# Python 2 and pip
sudo apt install python2

sudo apt install curl
curl https://bootstrap.pypa.io/pip/2.7/get-pip.py --output get-pip.py
sudo python2 get-pip.py

# Python 3 and pip
sudo apt install python3

sudo apt install python3-pip

## Installing DHALSIM dependencies
sudo pip install minicps

sudo pip install pathlib

sudo pip install pyyaml

sudo pip uninstall cpppo
sudo pip install cpppo==4.0.4

git clone git://github.com/mininet/mininet.git

PYTHON=python2 ~/mininet/util/install.sh -fnv

cd dhalsim

sudo python3 -m pip install -e .

printf "\nInstallation finished. You can now run DHALSIM by using \n\t\<sudo dhalsim your_config.yaml\>.\n"
