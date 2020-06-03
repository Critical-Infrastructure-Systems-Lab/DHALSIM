.. mitm {{{1
================================================================
Man in the Middle Attack between PLC1 and PLC2 in SCADA Topology
================================================================
.. }}}

.. INTRODUCTION {{{2
============
Introduction
============
The file automatic_mitm_attack.py performs a mitm attack between PLC1 and PLC2 in the scada topology scenario.

The attack only poisons the communication in the direction PLC1 --> PLC2, performing a replay attack. The attacker first sniffs 100 packets
and after of this, the attacks injects the sniffed packets back into the network. The attack requires to be run as sudo, it also netfilterqueue
library, which requires some other dependencies, for this reason I think is better to create a virtualenv

.. INSTALLATION {{{ 2
============
Installation
============

We need to install some netfilterqueue dependencies and scapy and netfilterqueue
for the sudo user, hence the use of a virtualenv

.. code-block:: console

    sudo apt-get install build-essential python-dev libnetfilter-queue-dev
    sudo apt-get install python-pip
    sudo apt-get install ettercap-text-only

    pip install virtualenv
    python -m virtualenv env

    source env/bin/activate

    sudo pip install scapy
    sudo pip install netfilterqueue

.. How to run {{{ 2
============
How to Run
============

We need to launch: The ICS topology, xterm consoles in the nodes, and launch the attack

i)   cd ~/thesis; make auto-mitm
ii)  in the mininet console: mininet> xterm plc1 plc2 attacker plant
     in plc1: plc1# python autuomatic_plc.py -n plc1
     in plc1: plc2# python autuomatic_plc.py -n plc2
     in plant: plant# automatic_plant.py
iii) in attacker: automatic_mitm_attack.py