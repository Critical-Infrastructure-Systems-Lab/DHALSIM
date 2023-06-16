Installation
============
In this guide, we will describe how DHALSIM can be installed on an Ubuntu machine. We offer two modes of installation, an automatic installation that uses a script that will install every dependency. In case the automatic installation is not able to complete, a walkthrough for a manual installation is also available.

Ubuntu version
~~~~~~~~~~~~~~~~~~~~~~~~
DHALSIM has been developed and tested on Ubuntu 20.04 LTS. Therefore, we recommend installing and running DHALSIM on Ubuntu 20.04. The installation script can be ran using ``./install.sh``. The installation script has not been tested on other versions. If you want to use another version, we recommend a manual installation.

The installation script can also install all testing and documentation dependencies. To do this, simply run ``./install.sh`` with the option `-t` for testing or `-d` for documentation, for example ``./install.sh -t -d``.
