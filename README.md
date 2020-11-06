# WadiTwin
Digital Twin for Water Distribution Systems. A work by the SUTD Resilient Water Systems Group and iTrust

This digital twin uses Mininet and MiniCPS to emulate the behavior of water distribution systems and the industrial control system controlling them. WadiTwin uses the WNTR EPANET wrapper to simulate the behaviour of water distribution systems. In addition to physical data, the digital twin emulates the industrial network and also generates .pcap files with this network data.
 
## How to use the Digital Twin

Install dependencies and clone the repository (see installation section below). The Makefile inside the ICS_topologies folder has entries to run each of the topologies. To run a topology use: 

```make topology entry```

All the topologies have a flag called "automatic" in the "automatic_run.py" script, giving that flag 1 will run automatically the topology. The results will be stored in a subfolder called "output"

## Installation

### Mininet and MiniCPS installation

This Digital Twin requies an Ubuntu 16.04 distribution, mininet, and MiniCPS installed. To install mininet, apt can be used:

The installation instructions for MiniCPS are found [here](https://github.com/scy-phy/minicps/blob/master/docs/userguide.rst)

### Virtual environment setup
The Digital Twin code requires ptyhon virtual environments set up in order to properly run with all the dependencies. Three environments will be used:

- A python 2.7 environment. The main environment in which Mininet and the topologies will be launched (Python 2.7)
- A python3.6 environment to launch the WNTR simulation and the water distribution simulations
- A puython2 environment to launch the man in the middle attacks

#### Python3.6 environment
Unfortunately, current WNTR version (0.2.2.1) requires at least a python3.6 environment. Instruction on setting a python3.6 environment in Ubuntu 16.04 can be found here: https://gist.github.com/plembo/c5bf7c4154910ac3693e14bb42b32ebf

#### Python3.6 virtual environment
The python3 venv can be installed using:
```pip3 install venv```

After the module has been installed, a virtual environment must be set up outside the Digital Twin root repository. The folder of this environment should be called "wntr-experiments"
```python3.6 -m venv wntr-experiments```

This environment can be activated using
```source wntr-experiments/bin/activate```

Inside this environment we will install the WNTR simulator and its dependencies with: 
```pip3 install wntr```

In addition the minitown 30 week simulation uses the sklearn package
```pip3 install sklearn```

This finishes the configuration of the python3 virtual environment

#### Python2 attack evnrionment
Some of the attacks use the python netfilterqueue and scapy to run properly. In addition, this modules should be installed for the sudo user. For this reason, we will set up an additional python2 environment. The python2 virtualenv package can be installed using: 
```pip2 install virtualenv``

After the module has been installed, a virtual environment must be set up outside the Digital Twin root repository. The folder of this environment should be called "attack-experiments"
```python2 -m virtualenv attack-experiments```

This environment can be activated using
```source attack-experiments/env/bin/activate```

Inside this environment we will install scapy and netfilterqueue
```pip2 install scapy netfilterqueue```

This finishes the configuration of the python2 virtual environment

## Repository Structure
This repository is mainly composed of three folders:
- ICS Topologies. This is the main folder, each subfolder represents a specific experiment using three topologies: minitown, c-town, and SUTD WADI
- Jupyter Notebooks. This subfolder has visualization jupyter notebooks
- Attack repository. This folder has scripts to launch mitm attacks

### ICS Topologies
This folder includes various subfolders. Each of this subfolders is an independent mininet and experiment topology. For all these folders, physical_process.py represents the physical process and each of the plcsX.py the behaviour of the PLCs. In addition the automatic_run.py file is used by mininet to launch the topologies and in some cases run the experiments automatically. At the end of the experiments and output folder will be created with both the physical and network data. 
The Makefile file has entries to run each of the simulations. For example, ctown can be launched using:

```make ctown```

### Attack Repository
This folder has files to run two network attacks into the plcs and scada. Man in the middle attacks and Denial of Service Attacks
