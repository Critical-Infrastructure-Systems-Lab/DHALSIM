Configuration
=============

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
The :code:`inp_file` option should be the path to the inp file to use in the experiment.
This can be either a absolute path, or relative to the configuration file.

cpa_file
------------------------
output_path
------------------------
iterations
------------------------
network_topology_type
------------------------
mininet_cli
------------------------
If the :code:`mininet_cli` option is :code:`True`, then after the network is setup, the mininet CLI interface will start.
See the `mininet tutorial on the CLI <http://mininet.org/walkthrough/#part-3-mininet-command-line-interface-cli-commands>`_ for more information
This option is by default set to :code:`False`.
:code:`mininet_cli` should be a boolean.

simulator
------------------------
