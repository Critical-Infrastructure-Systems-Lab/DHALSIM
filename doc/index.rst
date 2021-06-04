Welcome to DHALSIM's documentation!
===================================
A Digital Twin for Water Distribution Systems. A work by the SUTD Resilient Water Systems Group and iTrust, along with an undergrad development team at TU Delft.
This digital twin uses Mininet and MiniCPS to emulate the behavior of water distribution systems and the industrial control system controlling them.

DHALSIM uses the WNTR EPANET wrapper to simulate the behaviour of water distribution systems. In addition to physical data, the digital twin emulates the industrial
network and generates .pcap files with this network data.

DHALSIM was presented in the ICSS Workshop in ACSAC'20.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation.rst
   configuration.rst
   attacks.rst
   running.rst
   api.rst