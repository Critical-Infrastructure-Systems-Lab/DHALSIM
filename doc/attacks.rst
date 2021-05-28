Attacks
=======

DHALSIM has support for device attacks and network attakcs. This chapter will explain the configuration for these.



Device Attakcs
--------------

Device attacks are attacks that are performed at the PLC itself. Imagine it as attacks where the attacker has physical access to the PLC being attacked.

Example:

.. code-block:: yaml

   device_attacks:
     - name: "Close PRAW1 from iteration 5 to 10"
       trigger:
         type: time
         start: 5
         end: 10
       actuator: P_RAW1
       command: closed

The following sections will explain the different configuration parameters.

Name
~~~~
*This option is required*

This defines the name of the attack.

Trigger
~~~~~~~~
*This option is required*

This parameter defines when the attack is triggered. There are 4 different types of triggers:

* Timed attacks
    * :code:`time` - This is a timed attack. This means that the attack will start at a given iteration and stop at a given iteration
* Sensor attacks: These are attacks that will be triggered when a certain sensor in the water network meets a certain condition.
    * :code:`below` - This will make the attack trigger while a certain tag is below or equal to a given value
    * :code:`above` - This will make the attack execute while a certain tag is above or equal to a given value
    * :code:`between` - This will ensure that the attack is executed when a certain tag is between or equal to two given values

These are the required parameters per type of trigger:

* For :code:`time` attacks:
    * :code:`start` - The start time of the attack (in iterations).
    * :code:`end` - The end time of the attack (in iterations).
* For :code:`below` and :code:`above` attacks:
    * :code:`sensor` - The sensor of which the value will be used as the trigger.
    * :code:`value` - The value which has to be reached in order to trigger the attack.
* For :code:`between` attacks:
    * :code:`sensor` - The sensor of which the value will be used as the trigger.
    * :code:`lower_value` - The lower bound.
    * :code:`upper_value` - The upper bound.

Actuator
~~~~~~~~~
*This option is required*

This parameters defines the actuator on which the :code:`command` should be executed.

Command
~~~~~~~
*This option is required*

This parameter defines the command to be executed on the supplied :code:`actuator`. There are two possible commands:

* :code:`open` - Open the actuator
* :code:`closed` - Close the actuator


Examples
~~~~~~~~

Here is an example of a :code:`device_attacks` section in an attack YAML file:

.. code-block:: yaml

    device_attacks:
      - name: "Close PRAW1 from iteration 5 to 10"
       trigger:
         type: time
         start: 5
         end: 10
       actuator: P_RAW1
       command: closed
      - name: "Close PRAW1 when T2 < 0.16"
       trigger:
         type: below
         sensor: T2
         value: 0.16
       actuators: P_RAW1
       command: closed
      - name: "Close PRAW1 when 0.10 < T2 < 0.16"
       trigger:
         type: between
         sensor: T2
         lower_value: 0.10
         upper_value: 0.16
       actuators: P_RAW1
       command: closed

Network Attacks
---------------

Network attacks are attacks where a new node is added to the mininet network topology. This node is an
"attacker" and it can perform various attacks on the network. There are different types of attacks possible.
These are explained in the following sections.

Man-in-the-middle Attacks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Man-in-the-middle (MITM) attacks are attacks where the attacker will sit in between a PLC and its
connected switch. The attacker will then route all packets that are destined for the PLC through itself
and can for example modify the responses to the other PLCs.

.. figure:: static/complex_topo_attack.svg
    :align: center
    :alt: A complex topology with an attacker
    :figclass: align-center

    A complex topology with an attacker

Example
^^^^^^^^^^^^^^^^^^^^^^^^^

This is an example of a network attack definition:

.. code-block:: yaml

   device_attacks:
     name: "test1"
     type: mitm
     trigger:
       type: time
       start: 5
       end: 10
     tags:
       - tag: T0
         value: 0.1
       - tag: T2
         value: 0.2
     target: PLC1

The following sections will explain the configuration parameters.

Name
^^^^^^^^^^^^^^^^^^^^^^^^^
*This option is required*

This defines the name of the attack. It is also used as the name of the attacker node on the mininet network.

Type
^^^^^^^^^^^^^^^^^^^^^^^^^
*This option is required*

This defines the type of network attack. For a MITM attack this should be :code:`mitm`.

Trigger
^^^^^^^^^^^^^^^^^^^^^^^^^
*This option is required*

This parameter defines when the attack is triggered. There are 4 different types of triggers:

* Timed attacks
    * :code:`time` - This is a timed attack. This means that the attack will start at a given iteration and stop at a given iteration
* Sensor attacks: These are attacks that will be triggered when a certain sensor in the water network meets a certain condition.
    * :code:`below` - This will make the attack trigger while a certain tag is below or equal to a given value
    * :code:`above` - This will make the attack execute while a certain tag is above or equal to a given value
    * :code:`between` - This will ensure that the attack is executed when a certain tag is between or equal to two given values

These are the required parameters per type of trigger:

* For :code:`time` attacks:
    * :code:`start` - The start time of the attack (in iterations).
    * :code:`end` - The end time of the attack (in iterations).
* For :code:`below` and :code:`above` attacks:
    * :code:`sensor` - The sensor of which the value will be used as the trigger.
    * :code:`value` - The value which has to be reached in order to trigger the attack.
* For :code:`between` attacks:
    * :code:`sensor` - The sensor of which the value will be used as the trigger.
    * :code:`lower_value` - The lower bound.
    * :code:`upper_value` - The upper bound.

Tags
^^^^^^^^^^^^^^^^^^^^^^^^^
*This option is required*

This defines the tags that will be spoofed in a MITM attack. It contains a list of "tuples" defining the tag and the corresponding value or offset.

For example, to overwrite the value of T1:

.. code-block:: yaml

   tags:
     - tag: T1
       value: 0.12

Or instead, to offset the value of T1:

.. code-block:: yaml

   tags:
     - tag: T1
       offset: -0.2

Target
^^^^^^^^^^^^^^^^^^^^^^^^^
*This option is required*

This will define the target of the network attack. For a MITM attack, this is the PLC at which the attacker will sit.