.. dhalsim documentation master file, created by
   sphinx-quickstart on Mon May  3 22:03:50 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to DHALSIM's documentation!
===================================
A Digital Twin for Water Distribution Systems. A work by the SUTD Resilient Water Systems Group and iTrust

This digital twin uses Mininet and MiniCPS to emulate the behavior of water distribution systems and the industrial control system controlling them. WadiTwin uses the WNTR EPANET wrapper to simulate the behaviour of water distribution systems. In addition to physical data, the digital twin emulates the industrial network and also generates .pcap files with this network data.

DHALSIM was presented in the ICSS Workshop in ACSAC'20.

Installation
-------------
In order to offer a simple installation we have included an installation script which will install DHALSIM on an Ubuntu 20 machine. This script is located in the root of the repository. We recommend executing it using ```yes | ./install.sh```.

DHALSIM can also be installed manually for other Ubuntu versions. To this end you may use the following instructions.

Mininet and MiniCPS installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The installation instructions for MiniCPS and Mininet are found [here](https://github.com/scy-phy/minicps/blob/master/docs/userguide.rst). Please note that the cpppo install should be replaced by ```cpppo==4.0.4```.

Python 2 and pip
~~~~~~~~~~~~~~~~~~~~~~~~
DHALSIM requires Python 2, which is no longer automatically installed on newer versions of Ubuntu. Python 2 can be installed using ```sudo apt install python2```. You can get pip for Python 2 by ```curl https://bootstrap.pypa.io/pip/2.7/get-pip.py --output get-pip.py``` and subsequently ```sudo python2 get-pip.py```.

Other dependencies
~~~~~~~~~~~~~~~~~~~~~~
Finally DHALSIM needs pathlib and pyyaml installed. Other dependencies can be automatically installed using ```sudo python3 -m pip install -e``` in the root of the repository.

.. toctree::
   :maxdepth: 2
   :caption: Contents:



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. automodule:: dhalsim.static.plc_config
    :members: