# Digital HydrAuLic SIMulator (DHALSIM)
_A Digital Twin for Water Distribution Systems. A work by the SUTD Resilient Water Systems Group and iTrust_

This digital twin uses Mininet and MiniCPS to emulate the behavior of water distribution systems and the industrial control system controlling them. WadiTwin uses the WNTR EPANET wrapper to simulate the behaviour of water distribution systems. In addition to physical data, the digital twin emulates the industrial network and also generates .pcap files with this network data.

DHALSIM was presented in the ICSS Workshop in ACSAC'20.

## Installation

In order to offer a simple installation we have included an installation script which will install DHALSIM on an Ubuntu 20 machine. This script is located in the root of the repository. We recommend executing it using ```yes | ./install.sh```.

DHALSIM can also be installed manually for other Ubuntu versions. To this end you may use the following instructions.

### Mininet and MiniCPS installation

The installation instructions for MiniCPS and Mininet are found [here](https://github.com/scy-phy/minicps/blob/master/docs/userguide.rst). Please note that the cpppo install should be replaced by ```cpppo==4.0.4```.

### Python 2 and pip

DHALSIM requires Python 2, which is no longer automatically installed on newer versions of Ubuntu. Python 2 can be installed using ```sudo apt install python2```. You can get pip for Python 2 by ```curl https://bootstrap.pypa.io/pip/2.7/get-pip.py --output get-pip.py``` and subsequently ```sudo python2 get-pip.py```.

### Other dependencies

Finally DHALSIM needs pathlib and pyyaml installed. Other dependencies can be automatically installed using ```sudo python3 -m pip install -e``` in the root of the repository.

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

## Repository Structure
This repository is mainly composed of three folders:
- Demand Patterns: This folder contains auxiliary files to create and use customized demand patterns for hydraulic topologies
- ICS Topologies. This is the main folder, each subfolder represents a specific experiment using three topologies: minitown, c-town, and SUTD WADI
- Jupyter Notebooks. This subfolder has visualization jupyter notebooks
- Attack repository. This folder has scripts to launch mitm attacks

### ICS Topologies
This folder includes various subfolders. Each of this subfolders is an independent mininet and experiment topology. For all these folders, physical_process.py represents the physical process and each of the plcsX.py the behaviour of the PLCs. In addition the automatic_run.py file is used by mininet to launch the topologies and in some cases run the experiments automatically. At the end of the experiments and output folder will be created with both the physical and network data. 
The Makefile file has entries to run each of the simulations. For example, ctown can be launched using:

```make enhanced-ctown```

### Attack Repository
This folder has files to run two network attacks into the plcs and scada. Man in the middle attacks and Denial of Service Attacks
