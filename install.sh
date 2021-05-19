#!/bin/bash

cwd=$(pwd)

cd ~

sudo apt update

## Installing necessary packages
sudo apt install -y git

sudo apt install -y openvswitch-testcontroller

# Python 2 and pip
sudo apt install -y python2

sudo apt install -y curl
curl https://bootstrap.pypa.io/pip/2.7/get-pip.py --output get-pip.py
sudo python2 get-pip.py

# Python 3 and pipd
sudo apt install -y python3

sudo apt install -y python3-pip

# MiniCPS
git clone https://github.com/afmurillo/minicps.git
cd minicps
sudo python2 -m pip install .
cd ~

## Installing other DHALSIM dependencies
sudo pip install pathlib

sudo pip install pyyaml

sudo pip uninstall -y cpppo
sudo pip install cpppo==4.0.4

sudo apt install -y mininet

cd ${cwd}

sudo python3 -m pip install -e .

printf "\nInstallation finished. You can now run DHALSIM by using \n\t\<sudo dhalsim your_config.yaml\>.\n"
