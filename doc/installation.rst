Installation
============
In this guide, we will describe how DHALSIM can be installed on an Ubuntu machine. We offer two modes of installation, an automatic installation that uses a script that will install every dependency. In case the automatic installation is not able to complete, a walkthrough for a manual installation is also available.

Ubuntu version
~~~~~~~~~~~~~~~~~~~~~~~~
DHALSIM has been developed and tested on Ubuntu 20.04 LTS. Therefore, we recommend installing and running DHALSIM on Ubuntu 20.04. The installation script can be ran using ``./install.sh``. The installation script has not been tested on other versions. If you want to use another version, we recommend a manual installation.

The installation script can also install all testing dependencies. To do this, simply run ``./install.sh test``.

Automatic installation
----------------------
After cloning the repository, you can use the install script to install DHALSIM and its prerequisites.

.. prompt:: bash $

    git clone git@gitlab.ewi.tudelft.nl:cse2000-software-project/2020-2021-q4/cluster-06/water-infrastructure/dhalsim.git
    cd dhalsim
    sudo chmod +x install.sh
    ./install.sh

Manual installation
-------------------
DHALSIM can also be installed manually for other Ubuntu versions. To this end, you can use the following instructions.

Python and pip
~~~~~~~~~~~~~~~~~~~~~~~~
DHALSIM requires Python 2, which is no longer automatically installed on newer versions of Ubuntu. Python 2 can be installed using ``sudo apt install python2``. You can get pip for Python 2 by ``curl https://bootstrap.pypa.io/pip/2.7/get-pip.py --output get-pip.py`` and subsequently ``sudo python2 get-pip.py``.

Python 3 and ``python3-pip`` are also required.

Mininet and MiniCPS installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The installation instructions for MiniCPS and Mininet can be found `here
<https://github.com/scy-phy/minicps/blob/master/docs/userguide.rst>`_.

Please note that the cpppo installation should be replaced by ``cpppo==4.0.*``.

Other dependencies
~~~~~~~~~~~~~~~~~~~~~~
Finally, DHALSIM requires pathlib and pyyaml. Other Python 3 dependencies should be automatically installed with ``sudo python3 -m pip install -e .`` in the root of DHALSIM.
