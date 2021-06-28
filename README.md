# Digital HydrAuLic SIMulator (DHALSIM)
_A Digital Twin for Water Distribution Systems. A work by the SUTD Resilient Water Systems Group, iTrust, and TU Delft Department of Water Infrastructure_

DHALSIM uses the WNTR EPANET wrapper to simulate the behaviour of water distribution systems. In addition, DHALSIM uses Mininet and MiniCPS to emulate the behavior of industrial control system controlling a water distribution system. This means that in addition to physical data, DHALSIM can also provide network captures of the PLCs, SCADA server, and other network and industrial devices present in the a water distribution system.

DHALSIM was presented in the ICSS Workshop in ACSAC'20, with the paper: [Co-Simulating Physical Processes and Network Data for High-Fidelity Cyber-Security Experiments](https://dl.acm.org/doi/abs/10.1145/3442144.3442147)

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
