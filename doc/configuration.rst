Configuration
=======================

To run DHALSIM, you will need a configuration yaml file. In this chapter every parameter is explained.

Example with all options:

.. code-block:: yaml

    inp_file: wadi_map.inp
    cpa_file: wadi_cpa.yaml
    network_topology_type: complex
    output_path: output
    iterations: 500
    mininet_cli: False
    log_level: info
    simulator: pdd
    run_attack: True
    attacks_path: "attacks.yaml"
    batch_mode: false
    initial_tank_values: initial_tank.csv
    network_loss: true
    network_loss_data: losses.csv
    network_delay: false
    network_delay_data: delays.csv

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
    * Debug is a special kind of logging level: this will print all debug statements of DHALSIM, as well as all logs printed by MiniCPS and mininet. Since MiniCPS uses print statements as their logging system, MiniCPS will not use proper logging as we have implemented it.
* :code:`info`
    * Info will log DHALSIM info statements to the console. This is the default value for log_level and is recommended for use of DHALSIM.
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

batch_mode
------------------------
*This is an optional value with default*: :code:`False`

If the :code:`batch_mode` option is :code:`True`, then the simulation will be running in batch mode. This means you can provide :code:`.csv`
files with initial tank conditions, demand patterns, and network losses to simulate under different conditions. The full simulation will run
:code:`batch_iterations` number of times. (**NOTE, NONE OF THIS WORKS YET, JUST INITIAL VALUES**)
:code:`batch_mode` should be a boolean.

initial_tank_values
------------------------
*This is mandatory when batch mode is*: :code:`True`

The :code:`initial_tank_values` provides the name of the :code:`.csv` files with initial tank values for batch mode simulation. Each column should be a tank
with rows being initial values for each simulation. If you want to only provide initial values for some tanks, then you can do that and the remaining
tanks will use the default initial value from the :code:`.inp` file.

An example would look like this :

.. csv-table:: initial_tank_values
   :header: "tank_1", "tank_2", "tank_3"
   :widths: 5, 5, 5

    1.02,2.45,3.17
    4.02,5.45,6.17
    7.02,8.45,9.17

network_loss
------------------------
*This is an optional value with default*: :code:`False`

If the :code:`network_loss` option is :code:`True`, then the network simulation will run using network losses. This means you can provide a :code:`.csv`
file with network losses to simulate under non-perfect network conditions. If :code:`batch_mode` is :code:`False`, then the network losses used will be the first
row in the CSV. If :code:`batch_mode` is :code:`True` then it will use the same index as the tank levels, demand patterns, etc.
:code:`network_loss` should be a boolean.

network_loss_data
------------------------
*This is mandatory when network loss is*: :code:`True`

The :code:`network_loss_data` provides the name of the :code:`.csv` file with network loss values for the simulation. Each column should be a router
with rows being the loss values. If you want to only provide losses for some routers, then you can do that and the remaining
routers will use the default value (none).

An example would look like this :

.. csv-table:: network_loss_data
   :header: "r0", "r1", "r2"
   :widths: 5, 5, 5

    0.02,0.45,0.17
    0.03,0.46,0.18
    0.04,0.47,0.19

network_delay
------------------------
*This is an optional value with default*: :code:`False`

If the :code:`network_delay` option is :code:`True`, then the network simulation will run using network delays. This means you can provide a :code:`.csv`
file with network delays to simulate under non-perfect network conditions. If :code:`batch_mode` is :code:`False`, then the network delays used will be the first
row in the CSV. If :code:`batch_mode` is :code:`True` then it will use the same index as the tank levels, demand patterns, etc.
:code:`network_delay` should be a boolean.

network_delay_data
------------------------
*This is mandatory when network loss is*: :code:`True`

The :code:`network_delay_data` provides the name of the :code:`.csv` file with network delay values for the simulation. Each column should be a router
with rows being the delay values. If you want to only provide delays for some routers, then you can do that and the remaining
routers will use the default value (none).

An example would look like this :

.. csv-table:: network_delay_data
   :header: "r0", "r1", "r2"
   :widths: 5, 5, 5

    22.02,42.45,17.17
    22.03,42.46,17.18
    22.04,42.47,17.19