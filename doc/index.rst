DHALSIM  Documenation
=======================

DHALSIM is a Digital Twin for Water Distribution Systems. A work by the SUTD Critical Infrastructure Systems Lab, TU
Delft Department of Water Management, CISPA, and iTrust

DHALSIM uses the `WNTR <https://wntr.readthedocs.io/en/latest/index.html>`_ EPANET wrapper to simulate the behaviour of
water distribution systems. In addition, DHALSIM uses Mininet and MiniCPS to emulate the behavior of industrial control
system controlling a water distribution system. This means that in addition to physical data, DHALSIM can also provide
network captures of the PLCs, SCADA server, and other network and industrial devices present in the a water distribution
system.

The documentation is distributed in the following files:

* attacks: explains how to run experiments on DHALSIM with attacks, the available attacks, and a description of the
  attacks and its options
* configuration: includes information on how to configure DHALSIM experiments
* events: explains what are events in DHALSIM and how to run experiments with events
* installation: explains how to install DHALSIM
* user_guide: explains how to create a new topology in DHALSIM or how to use an existing topology
* developing: explains (broadly) how DHALSIM works and considerations for future development