Running
===========
To run DHALSIM, simply input the command :

.. prompt:: bash $

    sudo dhalsim path/to/config.yaml

Output
-------------
Once the simulation has finished, various output files will be produced at the location specified in the :code:`config.yaml` under :ref:`output_path`.

PCAP
~~~~~~~~~~~~~~~~
:code:`.pcap` files will be produced for every PLC in the network, along with the SCADA. They will have the format :code:`plc_name.pcap` and :code:`scada.pcap`.
These files capture the network traffic that the PLCs and SCADA produce, and can be viewed in a program like `Wireshark <https://www.wireshark.org/>`_.

CSV
~~~~~~~~~~~~~~~~
Two :code:`.csv` files will be produced, one by the water simulation software and one by the SCADA:

 * The :code:`ground_truth.csv` represents the *actual* values of all tanks, pumps, actuators, valves, etc. during the running of the simulation.
 * The :code:`scada_values.csv` represents the values seen over the network by the SCADA during the simulation, it will record sensor values and
   actuator states for every sensor or actuator belonging to a PLC in the network.

By differentiating between these, if a cyber attack takes place that masks the true value of a tank for example, the :code:`ground_truth.csv` will
show the real value and the :code:`scada_values.csv` will show the modified value from the attacker.

Configuration save
~~~~~~~~~~~~~~~~~~
For your convenience, all input files are automatically saved in the :code:`output_folder` specified in the configuration file. Using these input files, the exact same experiment can be recreated and ran later. In addition, a :code:`/configuration/readme_experiment.md` is provided. This file contains the most important information about the experiment. In addition, batch mode will have :code:`/configuration/readme_batch.md` in each batch output folder.