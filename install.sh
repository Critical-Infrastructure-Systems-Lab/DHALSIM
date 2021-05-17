#!/bin/bash

cd ~

git clone git://github.com/mininet/mininet.git

PYTHON=python2 ~/mininet/util/install.sh -fnv

git clone git@github.com:afmurillo/minicps.git

cd minicps

sudo apt uninstall cpppo

sudo apt install cpppo==4.0.4

sudo python2 -m pip install -r ~/minicps/requirements-dev.txt

sudo python2 -m pip install .

cd ~
