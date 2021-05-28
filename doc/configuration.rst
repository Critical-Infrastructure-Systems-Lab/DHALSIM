Configuration
=======================

To run DHALSIM, you will need a configuration yaml file. In this chapter every parameter is explained.

Example:

.. code-block:: yaml

    inp_file: wadi_map.inp
    cpa_file: wadi_cpa.yaml
    network_topology_type: complex
    output_path: output
    iterations: 500
    mininet_cli: False
    log_level: info
    simulator: pdd
    attacks_path: "wadi_attacks.yaml"

In the following sections, every entry is explained.

inp_file
------------------------
*This option is required*

The inp file is the file used primarily in the EPANET water simulation, it stores the description of the water network
along with simulation values such as duration; and control rules for valves, pumps, etc.

The :code:`inp_file` option should be the path to the inp file to use in the experiment.
This can be either a absolute path, or relative to the configuration file.

cpa_file
------------------------
*This option is required*

The :code:`cpa_file` is one of the mandatory input files to DHALSIM. It defines what PLCs are in the network, and which sensors/actuators
those PLCs control. The :code:`cpa_file` is a yaml file that contains a list of PLCs. A PLC has the following format:

.. code-block:: yaml

  - name: plc_name
    sensors:
      - sensor_1
      - sensor_2
    actuators:
      - actuator_1
      - actuator_2

Sensors are the tanks that are being monitored, and actuators would be valves and pumps.

Thus, an example yaml file would look as such:

.. code-block:: yaml

    plcs:
      - name: PLC1
        sensors:
          - Tank1
        actuators:
          - Pump1
          - Valve1
      - name: PLC2
        sensors:
          - Tank2
        actuators:
          - Valve2

The name of the :code:`cpa_file` must be defined in the :code:`config.yaml` under 'cpa_file',
this can be either a absolute path, or relative to the configuration file.

network_topology_type
--------------------------------
*This option is required*

This option represents the mininet network topology that will be used. It has two options, :code:`simple` and :code:`complex`.

If you use the :code:`simple` option, then a network topology will be generated that has all of the PLCs and the SCADA in one
local network. The PLCs connect to one switch and the SCADA to another, and those switches then connect to one router.

.. figure:: static/simple_topo.svg
    :align: center
    :alt: Diagram of a simple topology
    :figclass: align-center

    Diagram of simple topology

If you use the :code:`complex` option then a network topology will be generated that has all of the PLCs and the SCADA in their
own independent network. They will all have a switch and a router, these then connect to a central router through their public ip
addresses. This makes testing of attacks such as man in the middle more realistic.

.. figure:: static/complex_topo.svg
    :align: center
    :alt: Diagram of a complex topology
    :figclass: align-center

    Diagram of complex topology

output_path
------------------------
*This is an optional value with default*: :code:`output`

This option represents the path to the folder in which output files (.pcap, .csv, etc.) will be
created. The default is output and the path is relative to the configuration file.

iterations
------------------------
*This is an optional value with default*: duration / hydraulic time-step

The iterations value represents for how many iterations you would like the water simulation to run.
One iteration represents one hydraulic time-step.


log_level
------------------------
*This is an optional value with default*: :code:`info`

DHALSIM uses Python's built-in :code:`logging` module to log events. Using the `log_level` attribute in the configuration file, one can change the severity level of events that should be reported by DHALSIM. There are five different logging levels that are accepted, with each logging level also printing the logs of a higher priority. For example, setting `log_level` to `warning`, will log all `warning`, `error`, and `critical` statements to the console.

* :code:`debug`
    * Debug is a special kind of logging level: this will print all debug statements of DHALSIM, as well as all logs printed by MiniCPS and mininet. Since MiniCPS uses print statements as their logging system, MiniCPS will not be able to make use of our logging system.
* :code:`info`
    * Info will log DHALSIM info statements to the console. This is the default value for log_level and is recommended for normal use of DHALSIM.
* :code:`warning`
* :code:`error`
* :code:`critical`
    * Critical errors are errors that make DHALSIM crash. This will always be logged to the console.

mininet_cli
------------------------
*This is an optional value with default*: :code:`False`

If the :code:`mininet_cli` option is :code:`True`, then after the network is setup, the mininet CLI interface will start.
See the `mininet tutorial on the CLI <http://mininet.org/walkthrough/#part-3-mininet-command-line-interface-cli-commands>`_ for more information
:code:`mininet_cli` should be a boolean.

simulator
------------------------
*This is an optional value with default*: :code:`PDD`

The simulator option in the config file represents the demand model used by the WNTR simulation.
The valid options are :code:`PDD` and :code:`DD`. This value is then passed to the
`WNTR hydraulic demand model option <https://wntr.readthedocs.io/en/latest/hydraulics.html>`_.

attacks_path
------------------------
*This is an optional value*

This is the path, relative to the config file, to the attacks YAML file.
The contents of this file are described in the :ref:`Attacks` section.
If this option is left out, or commented out, the simulation will run without attacks.


