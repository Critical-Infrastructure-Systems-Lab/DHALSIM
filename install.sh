#!/bin/bash

ARG1=${1:-test}
cwd=$(pwd)
version=$(lsb_release -rs )

if [ "$version" != "20.04" ]
then
  echo "Warning! This installation script has only been tested on Ubuntu 20.04 LTS and will likely not work on other versions."
fi

if [ "$ARG1" != "test" ]
then
  echo "Installing without testing dependencies."
  sleep 3
else
  echo "Installing with testing dependencies."
  sleep 3
fi

# Update apt
sudo apt update

# Installing necessary packages
sudo apt install -y git python2 python3 python3-pip curl

# Get python2 pip
curl https://bootstrap.pypa.io/pip/2.7/get-pip.py --output get-pip.py
sudo python2 get-pip.py
rm get-pip.py

# CPPPO Correct Version 4.0.*
sudo pip install cpppo==4.0.*

# MiniCPS
cd ~
git clone --depth 1 https://github.com/afmurillo/minicps.git || git -C minicps pull
cd minicps
sudo python2 -m pip install .

## Installing other DHALSIM dependencies
sudo pip install pathlib==1.0.*
sudo pip install pyyaml==5.3.*

## Installing testing dependencies
if [ "$ARG1" != "test" ]
then
  sudo pip2 install netaddr==0.8.*
  sudo pip2 install flaky==3.7.*
  sudo pip2 install pytest==4.6.*
fi

# Mininet from source
cd ~
git clone --depth 1 -b 2.3.0 https://github.com/mininet/mininet.git || git -C mininet pull
cd mininet
sudo PYTHON=python2 ./util/install.sh -fnv

# Install DHALSIM
cd "${cwd}" || { echo "Failure: Could not find DHALSIM directory"; exit 1; }

if [ "$ARG1" != "test" ]
then
  sudo python3 -m pip install -e .
else
  sudo python3 -m pip install -e .[test]
fi
sudo service openvswitch-switch start

# Installation complete
printf "\nInstallation finished. You can now run DHALSIM by using \n\t<sudo dhalsim your_config.yaml>.\n"
