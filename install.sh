#!/bin/bash

cwd=$(pwd)

# Update apt
sudo apt update

# Installing necessary packages
sudo apt install -y git python2 python3 python3-pip curl

# Get python2 pip
curl https://bootstrap.pypa.io/pip/2.7/get-pip.py --output get-pip.py
sudo python2 get-pip.py
rm get-pip.py

# CPPPO Correct Version 4.0.4
sudo pip install cpppo==4.0.4

# MiniCPS
cd ~
git clone https://github.com/afmurillo/minicps.git || git -C minicps pull
cd minicps
sudo python2 -m pip install .

## Installing other DHALSIM dependencies
sudo pip install pathlib
sudo pip install pyyaml
sudo pip3 install progressbar2

# Mininet from source
cd ~
git clone https://github.com/mininet/mininet.git || git -C mininet pull
cd mininet
./util/install.sh -fnv

# Install DHALSIM
cd ${cwd}
sudo python3 -m pip install -e .

# Installation complete
printf "\nInstallation finished. You can now run DHALSIM by using \n\t\<sudo dhalsim your_config.yaml\>.\n"
