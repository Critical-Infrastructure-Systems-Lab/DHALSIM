#!/bin/bash

cwd=$(pwd)
version=$(lsb_release -rs )

doc=false
test=false

# Setting up test and doc parameters
while getopts ":dt" opt; do
  case $opt in
    d)
      printf "Installing with documentation dependencies.\n"
      doc=true
      ;;
    t)
      printf "Installing with testing dependencies.\n"
      test=true
      ;;
    \?)
      printf "Unknown option. Proceeding without installing documentation and testing dependencies.\n"
      ;;
  esac
done

sleep 3

# Update apt
sudo apt update

# Installing necessary packages
sudo apt install -y git python3 python3-pip curl
sudo python3 -m pip install cpppo

# MiniCPS
cd ~
git clone --depth 1 https://github.com/scy-phy/minicps.git || git -C minicps pull
cd minicps
sudo python3 -m pip install .

# epynet - An EPANET Python wrapper for WNTR
cd ~
git clone --depth 1 https://github.com/afmurillo/DHALSIM-epynet || git -C DHALSIM-epynet pull
cd DHALSIM-epynet/
sudo python3 -m pip install .

# Mininet from source
cd ~
git clone --depth 1 -b 2.3.1b4 https://github.com/mininet/mininet.git || git -C mininet pull
cd mininet
sudo PYTHON=python3 ./util/install.sh -fnv

# Installing testing pip dependencies
if [ "$test" = true ]
then
  sudo python3 -m pip install pytest-timeout
  sudo python3 -m pip install pytest-cov
  sudo python3 -m pip install pytest-mock
fi

# Install netfilterqueue for Simple DoS attacks
sudo apt install -y libnfnetlink-dev libnetfilter-queue-dev
sudo python3 -m pip install -U git+https://github.com/kti/python-netfilterqueue

# Install DHALSIM
cd "${cwd}" || { printf "Failure: Could not find DHALSIM directory\n"; exit 1; }

# Install without doc and test
if [ "$test" = false ] && [ "$doc" = false ]
then
  sudo python3 -m pip install -e .

  printf "\nInstallation finished. You can now run DHALSIM by using \n\t<sudo dhalsim your_config.yaml>.\n"
  exit 0;
fi

# Install doc
if [ "$test" = false ]
then
  sudo python3 -m pip install -e .[doc]

  printf "\nInstallation finished. You can now run DHALSIM by using \n\t<sudo dhalsim your_config.yaml>.\n"
  exit 0;
fi

# Install test
if [ "$doc" = false ]
then
  sudo python3 -m pip install -e .[test]

  printf "\nInstallation finished. You can now run DHALSIM by using \n\t<sudo dhalsim your_config.yaml>.\n"
  exit 0;
fi

# Install test and doc
sudo python3 -m pip install -e .[test,doc]

printf "\nInstallation finished. You can now run DHALSIM by using \n\t<sudo dhalsim your_config.yaml>.\n"
exit 0;
