Attacks
=======

DHALSIM has support for device attacks and network attakcs. This chapter will explain the configuration for these.



Device Attakcs
--------------

Device attacks are attacks that are performed at the PLC itself. Imagine it as attacks where the attacker has physical access to the PLC being attacked.

Example:

.. code-block:: yaml

  name: "Close PRAW1 from iteration 5 to 10"
  type: "Time"
  actuators:
    - P_RAW1
  command: "closed"
  start: 5
  end: 10

The following sections will explain the different configuration parameters.

Name
~~~~
*This option is required*

This defines the name of the attack.

Type
~~~~
*This option is required*

This parameter defines the type of the device attack. There are four attack types that can be chosen from:

* Timed attacks
    * :code:`Time` - This is a timed attack. This means that the attack will start at a given iteration and stop at a given iteration
* Condition attacks: These are attacks that will be triggered when a certain condition gets met in the water network.
    * :code:`Below` - This will make the attack trigger while a certain tag is below a given value
    * :code:`Above` - This will make the attack execute while a certain tag is above a given value
    * :code:`Between` - This will ensure that the attack is executed when a certain tag is between two given values

Actuators
~~~~~~~~~
*This option is required*

This parameters defines the actuators on which the :code:`command` should be executed. This should be a list.

For example:

.. code-block:: yaml

  actuators:
    - P_RAW1
    - P_RAW2

Command
~~~~~~~
*This option is required*

This parameter defines the command to be executed on the supplied :code:`actuators`. There are two possible commands:

* :code:`open` - Open the actuators
* :code:`closed` - Close the actuators

Type-dependent Parameters
~~~~~~~~~~~~~~~~~~~~~~~~~
*All mentioned parameters (depending on the selected type) are required*

Depending on your :code:`type` parameter, some extra parameters should be provided:

* For :code:`Time` attacks:
    * :code:`start` - The start time of the attack (in iterations).
    * :code:`end` - The end time of the attack (in iterations).
* For :code:`Below` and :code:`Above` attacks:
    * :code:`sensor` - The sensor of which the value will be used as the trigger.
    * :code:`value` - The value which has to be reached in order to trigger the attack.
* For :code:`Between` attacks:
    * :code:`sensor` - The sensor of which the value will be used as the trigger.
    * :code:`lower_value` - The lower bound.
    * :code:`upper_value` - The upper bound.

Examples
~~~~~~~~

Here is an example of a :code:`device_attacks` section in an attack YAML file:

.. code-block:: yaml

    device_attacks:
      - name: "Close PRAW1 from iteration 5 to 10"
        type: Time
        actuators:
          - P_RAW1
        command: closed
        start: 5
        end: 10
      - name: "Close PRAW1 when T2 < 0.16"
        type: Below
        actuators:
          - P_RAW1
        command: closed
        sensor: T2
        value: 0.16
      - name: "Close PRAW1 when 0.10 < T2 < 0.16"
        type: Between
        actuators:
          - P_RAW1
        command: closed
        sensor: T2
        lower_value: 0.10
        upper_value: 0.16

Network Attacks
---------------

Network attacks are attacks where a new node is added to the mininet network topology. This node is an
"attacker" and it can perform various attacks on the network.

Network attack types
~~~~~~~~~~~~~~~~~~~~~

Man-in-the-middle Attacks
^^^^^^^^^^^^^^^^^^^^^^^^^

Man-in-the-middle (MITM) attacks are attacks where the attacker will sit in between a PLC and its
connected switch. The attacker will then route all packets that are destined for the PLC through itself
and can for example modify the responses to the other PLCs.

.. figure:: static/complex_topo_attack.svg
    :align: center
    :alt: A complex topology with an attacker
    :figclass: align-center

    A complex topology with an attacker

Example
~~~~~~~

This is an example of a network attack definition:

.. code-block:: yaml

    name: "test1"
    type: mitm
    start: 10
    end: 15
    tags:
      - tag: T0
        value: 0.1
      - tag: T2
        value: 0.2
    target: PLC1

The following sections will explain the configuration parameters.

Name
~~~~
*This option is required*

This defines the name of the attack. It is also used as the name of the attacker node on the mininet network.

Type
~~~~
*This option is required*

This defines the type of network attack. Currently, only one type is supported:

* :code:`mitm` - This defines the attack as a man-in-the-middle-attack.

Start
~~~~~
*This option is required*

This defines the start time of the attack (in iterations).

End
~~~
*This option is required*

This defines the end time of the attack (in iterations).

Tags
~~~~
*This option is required*

This defines the tags that will be spoofed in a MITM attack. It contains a list of "tuples" defining the tag and the corresponding value or offset.

For example, to overwrite the value of T1:

.. code-block:: yaml

    tags:
        tag: T1
        value: 0.12

Or instead, to offset the value of T1:

.. code-block:: yaml

    tags:
        tag: T1
        offset: -0.2

Target
~~~~~~
*This option is required*

This will define the target of the network attack. For a MITM attack, this is the PLC at which the attacker will sit.