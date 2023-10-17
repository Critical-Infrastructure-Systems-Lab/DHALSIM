# Digital HydrAuLic SIMulator (DHALSIM)
_A Digital Twin for Water Distribution Systems. A work by the SUTD Critical Infrastructure Systems Lab, TU Delft Department of Water Management, CISPA, and iTrust_

DHALSIM uses the [WNTR](https://wntr.readthedocs.io/en/latest/index.html) EPANET wrapper to simulate the behaviour of water distribution systems. In addition, DHALSIM uses Mininet and MiniCPS to emulate the behavior of industrial control system controlling a water distribution system. This means that in addition to physical data, DHALSIM can also provide network captures of the PLCs, SCADA server, and other network and industrial devices present in the a water distribution system.

DHALSIM was presented in the ICSS Workshop in ACSAC'20, with the paper: [Co-Simulating Physical Processes and Network Data for High-Fidelity Cyber-Security Experiments](https://dl.acm.org/doi/abs/10.1145/3442144.3442147)

Two papers in the Journal of Water Resources Planning and Management explain in detail DHALSIM architecture, features, and capabilities: [High-fidelity cyber and physical simulation of water distribution systems. I: Models and Data](https://ascelibrary.org/doi/abs/10.1061/JWRMD5.WRENG-5853) and [High-fidelity cyber and physical simulation of water distribution systems. II: Enabling cyber-physical attack localization](https://ascelibrary.org/doi/abs/10.1061/JWRMD5.WRENG-5854)
 
## Installation

In order to offer a simple installation we have included an installation script which will install DHALSIM on an Ubuntu 20.04 machine. This script is located in the root of the repository and can be run with ```./install.sh```.

## Running

DHALSIM can be run using the command ```sudo dhalsim path/to/config.yaml```.

Replacing the text between "< >" with the path to one example topology or your own configuration files. For example, for the anytown example, you'd use:
```sudo dhalsim <examples/anytown_topology/anytown_config.yaml>```