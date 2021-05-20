Configuration
=======================

To run dhalsim, you will need a configuration yaml file. In the chapter every parameter is explained.

Example:

.. code-block:: yaml

    inp_file: wadi_map.inp
    cpa_file: wadi_cpa.yaml
    output_path: output
    iterations: 500
    network_topology_type: complex
    mininet_cli: False
    simulator: pdd

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

network_topology_type
--------------------------------
*This option is required*

This option represents the mininet network topology that will be used. It has two options, :code:`simple` and :code:`complex`.

If you use the :code:`simple` option, then a network topology will be generated that has all of the PLCs and the SCADA in one
local network. The PLCs connect to one switch and the SCADA to another, and those switches then connect to one router.

.. figure:: static/simple_topo.svg
    :align: center
    :alt: Diagram of simple topology
    :figclass: align-center

    Diagram of simple topology

If you use the :code:`complex` option then a network topology will be generated that has all of the PLCs and the SCADA in their
own independent network. They will all have a switch and a router, these then connect to a central router through their public ip
addresses. This makes testing of attacks such as man in the middle more realistic.

.. figure:: static/complex_topo.svg
    :align: center
    :alt: Diagram of complex topology
    :figclass: align-center

    Diagram of complex topology

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

