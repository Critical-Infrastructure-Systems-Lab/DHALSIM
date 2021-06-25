# Digital HydrAuLic SIMulator (DHALSIM)
A Digital Twin for Water Distribution Systems. A work by the SUTD Resilient Water Systems Group and iTrust

DHALSIM uses the WNTR EPANET wrapper to simulate the behaviour of water distribution systems. In addition, DHALSIM uses Mininet and MiniCPS to emulate the behavior of industrial control system controlling a water distribution system. This means that in addition to physical data, DHALSIM can also provide network captures of the PLCs, SCADA server, and other network and industrial devices present in the a water distribution system.

DHALSIM was presented in the ICSS Workshop in ACSAC'20, with the paper: [Co-Simulating Physical Processes and Network Data for High-Fidelity Cyber-Security Experiments](https://dl.acm.org/doi/abs/10.1145/3442144.3442147)

## Installation

Installation should use a regular "unprivileged" user. In some cases, a sudo password will be required

### Mininet and MiniCPS installation
This Digital Twin requies an Ubuntu 16.04 distribution, mininet, and MiniCPS installed. To install mininet, apt can be used:

#### Mininet Installation
Mininet can be installed using aptitute

`$: sudo apt-get install mininet`

#### MiniCPS Installation
DHALSIM requires an updated version of MiniCPS that enables devices to send and receive multiple tags using the same ENIP connection.
Current master branch of MiniCPS does not support such function. [A pull request has been created here](https://github.com/scy-phy/minicps/pull/27)
Meanwhile, this [fork](https://github.com/afmurillo/minicps) provides such function. To install this fork follow the normal MiniCPS [installation instructions](https://github.com/afmurillo/minicps/blob/master/docs/userguide.rst)
A small note into the requirements, MiniCPS requires python-cpppo version 4.0.4. To install this version, use

`$: pip2 install cpppo=4.0.4`

At this point, MiniCPS can be tested by running the swat-s1 example. In order to do this:
1) Make sure that an X11 server is present in the machine or X11 is being forwarded to a proper display
2) Install xterm

`$: sudo apt-get install xterm`

3) Follow the [instructions](https://github.com/afmurillo/minicps/blob/master/docs/swat-tutorial.rst) to run the swat-s1 example

### Virtual environment setup
The Digital Twin code requires python virtual environments set up in order to properly run with all the dependencies. Three environments will be used:

- A python 2.7 environment. The main environment in which Mininet and the topologies will be launched (Python 2.7)
- A python3.6 environment to launch the WNTR simulation and the water distribution simulations
- A python2 environment to launch the man in the middle attacks

#### Python3.6 environment
Current WNTR version (0.3.0) requires at least a python3.6 environment. Instruction on setting a python3.6 environment in Ubuntu 16.04 can be found [here](https://www.tecmint.com/install-python-in-ubuntu/)

#### Python3.6 pip installation
After Python3.6 has been installed in the machine, pip can be installed using:
`$: sudo apt-get install python3-pip` 

#### Python3.6 virtual environment
The python3 venv can be installed using:
```:$ sudo apt-get install python3.6-venv```

After the module has been installed, a virtual environment must be set up outside the Digital Twin root repository. The folder of this environment should be called "wntr-experiments"
```:$ python3.6 -m venv wntr-experiments```

This environment can be activated using
```:$ source wntr-experiments/bin/activate```

Inside this environment we will install the WNTR simulator and its dependencies with: 
```:$ pip3 install wntr```

In addition the minitown 30 week simulation uses the sklearn package
```:$ pip3 install sklearn```

This finishes the configuration of the python3 virtual environment

#### Python2 attack environment
Some of the attacks use the python netfilterqueue and scapy to run properly. In addition, these modules should be installed for the sudo user. For this reason, we will set up an additional python2 environment. The python2 virtualenv package can be installed using: 
```:$ pip2 install virtualenv``

After the module has been installed, the netfilterqueue prerequisites must be installed. aptitude can be used with:
`:$ sudo apt-get install build-essential python-dev libnetfilter-queue-dev`
 
 a virtual environment must be set up outside the Digital Twin root repository. The folder of this environment should be called "attack-experiments"
```:$ python2 -m virtualenv attack-experiments```

This environment can be activated using
```:$ source attack-experiments/bin/activate```

Inside this environment we will install scapy and netfilterqueue
```:$ pip2 install scapy netfilterqueue```

This finishes the configuration of the python2 virtual environment

#### DHALSIM Epynet
The enhanced-ctown topology example does not use WNTR as a hydraulic simulator. Instead, it is configured to use the experimental as physical process simulator DHALSIM-epynet library developed by Davide Salaorni.
DHALSIM-epynet is a wrapper around EPANET2.2 and runs in a more natively way the EPANET simulator. Future releases of DHALSIM will have configured DHALSIM-epynet by default.

To install DHALSIM-epynet, clone the repository at: https://github.com/Daveonwave/DHALSIM-epynet.git

And create a symbolic link to the enhanced c-town topology:

 ln -s ~/DHALSIM-epynet/ ~/DHALSIM/ICS_topologies/enhanced_ctown_topology/
 
 In future versions, DHALSIM-epynet will be released as Python pip module.   
 

## How to use the Digital Twin

The Makefile inside the ICS_topologies has example topologies already implemented. To run an example topology use: 

```$: make topology entry```

All the topologies have a flag called "automatic" in the "automatic_run.py" script, giving that flag 1 will run automatically the topology. The results will be stored in a subfolder called "output"


## DHALSIM Modes of use

DHALSIM can be used in two ways: i) an automatic mode, ii) as an API to build and customize water distribution ICS topologies. 

### DHALSIM Automatic Mode
The automatic mode code is stored in the ICS_Topologies/general folder and uses the script "launch_dhalsim_experiment.sh" to launch a DHALSIM experiment. This script takes as a parameter the name of the topology to be used in the experiment. A topology is defined by the following files: i) an EPANET inp file, an epanetCPA file (only the cybernodes section is required), and a .yaml experiment configuration file. 
The EPANET file describes the hydraulic mode; the epanetCPA file describes which PLC handles what sensor or actuator; the experiment .yaml configuration is used to configure the experiment, "ICS_topologies/enhanced_ctown_topology/c_town_config.yaml" and "ICS_topologies/general/ky3.yaml" are examples of these files. 
When the script is launched, DHALSIM will read the EPANET and epanetCPA files and automatically build and launch a Mininet topology, using the experiment configuration defined in the .yaml file. After the exerpiment finishes, the results of the experiment will be stored in an "output" folder or "week_x" folder; this depends on the configurations defined in the .yaml file. 
This is an experimental feature. For now, only the example topologies implemented in the subfolder ICS_topologies are tested.
 
### DHALSIM API
The DHALSIM API can be used to build customized ICS topologies for a water distribution system. To create a custom topology, the following process should be realized:
i) Create a different folder into ICS_Topologies
ii) Copy the files: "automatic_run.py, automatic_plc.py, automatic_plant.py, basePLC.py, create_log_files.sh, copy_output.sh, ctown_nat.sh, init.py, kill_cppo.sh, physical_process.py, port_forward.sh, topo.py" into the new folder, these files would rarely need to be changed. "automatic_run" is the master script of the experiment. "automatic_plc" launches the tcp_dump process for a PLC node and its appropriate plc intance process. basePLC can be extended by a plc script to implement some functions automatically. "automatic_plant" and "physical_process" are scripts used to model the plant, physical_process requires an EPANET file to import a water network model.
iii) Modify or create the necessary scripts. In most cases, this implies creating scripts for PLC and SCADA behavior and script to implement new attacks
iv) Create an entry into the Makefile folder, or a script to launch the experiment (to create the experiment, the examples already present in the Makefile can be used as base)
v) Launch the experiment

#### EXample Topologies

Some example topologies and use cases are provided: minitown, ky3, WADI (based in [SUTD Wadi](https://itrust.sutd.edu.sg/testbeds/water-distribution-wadi/) ), and C-Town.

Each topology is defined in a folder. For all these folders, physical_process.py represents the physical process and each of the plcsX.py the behaviour of the PLCs. In addition the automatic_run.py file is used by mininet to launch the topologies and in some cases run the experiments automatically. At the end of the experiments and output folder will be created with both the physical and network data. 
The Makefile file has entries to run each of the simulations. For example, C-Town can be launched using:

```make enhanced-ctown```

## Repository Structure
This repository is mainly composed of three folders:
- Demand Patterns: This folder contains auxiliary files to create and use customized demand patterns for hydraulic topologies
- ICS Topologies. This is the main folder, each subfolder represents a specific experiment using three topologies: minitown, c-town, and SUTD WADI
- Jupyter Notebooks. This subfolder has visualization jupyter notebooks
- Attack repository. This folder has scripts to launch mitm attacks

### Attack Repository
This folder has files to run two network attacks into the plcs and scada. Man in the middle attacks and Denial of Service Attacks