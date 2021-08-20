Attacks
=======

DHALSIM has support for device attacks and network attacks. This chapter will explain the configuration for these.

If you want to put the attacks in a separate file, see the section :ref:`Attacks in a separate file`.

device attacks
--------------

Device attacks are attacks that are performed at the PLC itself. Imagine it as attacks where the attacker has physical access to the PLC being attacked.

Example:

.. code-block:: yaml

   device_attacks:
     - name: "Close_PRAW1_from_iteration_5_to_10"
       trigger:
         type: time
         start: 5
         end: 10
       actuator: P_RAW1
       command: closed

The following sections will explain the different configuration parameters.

name
~~~~
*This option is required*

This defines the name of the attack. It cannot have whitespaces.

trigger
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

actuator
~~~~~~~~~
*This option is required*

This parameter defines the actuator on which the :code:`command` should be executed.

command
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
      - name: "Close_PRAW_from_iteration_5_to_10"
       trigger:
         type: time
         start: 5
         end: 10
       actuator: P_RAW1
       command: closed
      - name: "Close_PRAW1_when_T2_<_0.16"
       trigger:
         type: below
         sensor: T2
         value: 0.16
       actuators: P_RAW1
       command: closed
      - name: "Close_PRAW1_when_0.10_<_T2_<_0.16"
       trigger:
         type: between
         sensor: T2
         lower_value: 0.10
         upper_value: 0.16
       actuators: P_RAW1
       command: closed

network attacks
---------------

Network attacks are attacks where a new node is added to the mininet network topology. This node is an
"attacker" and can perform various attacks on the network. There are different types of attacks possible.
These are explained in the following sections.

Man-in-the-middle Attack
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Man-in-the-middle (MITM) attacks are attacks where the attacker will sit in between a PLC and its
connected switch. The attacker will then route host a CPPPO server and respond to the CIP requests
for the PLC.

.. figure:: static/simple_topo_attack.svg
    :align: center
    :alt: A simple topology with an attacker
    :figclass: align-center
    :width: 50%

    A simple topology with an attacker

.. figure:: static/complex_topo_attack.svg
    :align: center
    :alt: A complex topology with an attacker
    :figclass: align-center
    :width: 50%

    A complex topology with an attacker


This is an example of a :code:`mitm` attack definition:

.. code-block:: yaml

   network_attacks:
     - name: attack1
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

name
^^^^^^^^^^^^^^^^^^^^^^^^^
*This option is required*

This defines the name of the attack. It is also used as the name of the attacker node on the mininet network.
The name can only contain the the characters :code:`a-z`, :code:`A-Z`, :code:`0-9` and :code:`_`. And
must have a length between 1 and 10 characters.

type
^^^^^^^^^^^^^^^^^^^^^^^^^
*This option is required*

This defines the type of network attack. For a MITM attack, this should be :code:`mitm`.

trigger
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

tags
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

target
^^^^^^^^^^^^^^^^^^^^^^^^^
*This option is required*

This will define the target of the network attack. For a MITM attack, this is the PLC at which the attacker will sit.

Naive Man-in-the-middle Attack
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Naive Man-in-the-middle (MITM) attacks are attacks where the attacker will sit in between a PLC and its
connected switch. The attacker will then route all TCP packets that are destined for the PLC through itself
and can for example modify the responses to the other PLCs.

.. figure:: static/simple_topo_attack.svg
    :align: center
    :alt: A simple topology with an attacker
    :figclass: align-center
    :width: 50%

    A simple topology with an attacker

.. figure:: static/complex_topo_attack.svg
    :align: center
    :alt: A complex topology with an attacker
    :figclass: align-center
    :width: 50%

    A complex topology with an attacker


This is an example of a :code:`naive_mitm` attack definition:

.. code-block:: yaml

   network_attacks:
     name: "test1"
     type: naive_mitm
     trigger:
       type: time
       start: 5
       end: 10
     value: 0.2
     target: PLC1
     direction: destination

The following sections will explain the configuration parameters.

name
^^^^^^^^^^^^^^^^^^^^^^^^^
*This option is required*

This defines the name of the attack. It is also used as the name of the attacker node on the mininet network.
The name can only contain the the characters :code:`a-z`, :code:`A-Z`, :code:`0-9` and :code:`_`. And
must have a length between 1 and 10 characters.

type
^^^^^^^^^^^^^^^^^^^^^^^^^
*This option is required*

This defines the type of network attack. For a Naive MITM attack, this should be :code:`naive_mitm`.

trigger
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

value/offset
^^^^^^^^^^^^^^^^
*One of these options is required*

If you want to overwrite everything with an absolute value, use the :code:`value` option, and set it to the desired value.
If you want to overwrite everything with a relative value, use the :code:`offset` option, and set it to the desired offset.

target
^^^^^^^^^^^^^^^^^^^^^^^^^
*This option is required*

This will define the target of the network attack. For a MITM attack, this is the PLC at which the attacker will sit.

direction
^^^^^^^^^^^^^^^^^^^^^^^^^
*This an optional parameter*

This will define the direction of the communication that we are launching the MiTM attack. Messages can be intercepted if the target is the "source" or "destination" of the messages. The valid values for this parameter are "source" and "destionation", the default value is "source"

<<<<<<< HEAD
=======

>>>>>>> 9c89a04 (Update attacks.rst)
Simple Denial of Service Attack
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This attack interrupts the flow of CIP messages containing data between PLCs. This attack first performs an ARP Spoofing attack into the target and then stops forwarding the CIP messages. This will cause the PLCs to be unable to update their cache with new system state information. Possibly taking wrong control action decisions.

This is an example of a :code:`simple_dos` attack definition:

.. code-block:: yaml

    network_attacks:
        - name: plc1attack
          target: PLC2
          trigger:
            type: time
            start: 648
            end: 936
          type: simple_dos
          direction: source
   
The following sections will explain the configuration parameters.

name
^^^^^^^^^^^^^^^^^^^^^^^^^
*This option is required*

This defines the name of the attack. It is also used as the name of the attacker node on the mininet network.
The name can only contain the the characters :code:`a-z`, :code:`A-Z`, :code:`0-9` and :code:`_`. And
must have a length between 1 and 10 characters.

trigger
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

target
^^^^^^^^^^^^^^^^^^^^^^^^^
*This option is required*

This will define the target of the network attack. For a MITM attack, this is the PLC at which the attacker will sit.

direction
^^^^^^^^^^^^^^^^^^^^^^^^^
*This an optional parameter*

This will define the direction of the communication that we are launching the MiTM attack. Messages can be intercepted if the target is the "source" or "destination" of the messages. The valid values for this parameter are "source" and "destionation", the default value is "source"
