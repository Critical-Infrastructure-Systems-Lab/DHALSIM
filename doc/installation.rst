Installation
============
In this guide, we will describe how DHALSIM can be installed on an Ubuntu 22.04 machine. DHALSIM installation is done automatically throuh the provided script that will install every dependency.

Ubuntu version
~~~~~~~~~~~~~~~~~~~~~~~~
DHALSIM has been developed and tested on Ubuntu 22.04 LTS. Therefore, we recommend installing and running DHALSIM on Ubuntu 22.04. The installation script can be ran using ``./install.sh``. The installation script has not been tested on other versions. If you want to use another version, we recommend a manual installation.

The installation script can also install all testing and documentation dependencies. To do this, simply run ``./install.sh`` with the option `-t` for testing or `-d` for documentation, for example ``./install.sh -t -d``.

Automatic installation
----------------------
After cloning the repository, you can use the install script to install DHALSIM and its prerequisites.

.. prompt:: bash $

    git clone git@github.com:afmurillo/DHALSIM.git
    cd dhalsim
    sudo chmod +x install.sh
    ./install.sh
