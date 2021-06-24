# Digital HydrAuLic SIMulator (DHALSIM)
_A Digital Twin for Water Distribution Systems. A work by the SUTD Resilient Water Systems Group, iTrust and TU Delft Department of Water Infrastructure_

This digital twin uses Mininet and MiniCPS to emulate the behavior of water distribution systems and the industrial control system controlling them. In addition to physical data, the digital twin emulates the industrial network and also generates .pcap files with this network data. Several example topologies with attacks have been provided in the examples folder.

DHALSIM was presented in the ICSS Workshop in ACSAC'20.

## Installation

In order to offer a simple installation we have included an installation script which will install DHALSIM on an Ubuntu 20.04 machine. This script is located in the root of the repository and can be run with ```./install.sh```.

DHALSIM can also be installed manually for other Ubuntu versions. To this end you may use the following instructions.

### Manual installation
#### Mininet and MiniCPS installation

The installation instructions for Mininet are found [here](https://github.com/scy-phy/minicps/blob/master/docs/userguide.rst). Please note that the cpppo install should be replaced by ```cpppo==4.0.4```. MiniCPS should be pulled from [this](https://github.com/afmurillo/minicps.git) repository.

#### Python 2 and pip

DHALSIM requires Python 2, which no longer comes installed on newer versions of Ubuntu. Python 2 can be installed using ```sudo apt install python2```. You can get pip for Python 2 by ```curl https://bootstrap.pypa.io/pip/2.7/get-pip.py --output get-pip.py``` and ```sudo python2 get-pip.py```.

#### Other dependencies

Finally, DHALSIM needs pathlib and pyyaml installed. Other dependencies should be automatically installed using ```sudo python3 -m pip install -e``` in the root of the repository.

## Running

DHALSIM can be run using the command ```sudo dhalsim path/to/config.yaml```.

## Repository structure

The repository is structured as follows. The ```dhalsim``` package contains all source files and the ```test``` package contains all tests. Documentation can be found in the ```doc``` folder. Some example topologies and configurations can be found in the ```examples``` folder. An important file in the root is the installation script ```install.sh```.