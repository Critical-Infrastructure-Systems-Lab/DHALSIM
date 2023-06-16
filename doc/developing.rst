Developing (and exetending) DHALSIM
===================================

This article explains (broadly and hastily) some design considerations of DHALSIM. These considerations might be useful
to help future developers into troubleshooting DHALSIM issues, adding functionalities, or adapting DHALSIM to their
needs.

DHALSIM is a Co-Simulation environment
--------------------------------------

DHALSIM was born at the idea of following the work that Riccardo Taormina did with epanetCPA. That is, to offer a
simulation tool that could provide not only physical information about a water distribution system (WDS) simulation,
but also realistic network traffic commonly seen in the Industrial Control Systems (ICS) that control systems such as
those present in WDS.

Because of this design principle, DHALSIM runs concurrently two things:

* An EPANET simulation, using either WNTR or epynet as a wrapper. Since it is a simulation, it runs on a step-by-step
  basis
* A MiniCPS emulation. Since MiniCPS is built on top of Mininet, this means that a container-based virtual network is
  running in a continuous way.

This architecture requires an element that allows communication between these two main modules. That is the reason of
using an SQLite database in DHALSIM. The database is used to exchange information between EPANET/MiniCPS. A DHALSIM
simulation is composed of a number of each iteration. On each iteration:

1. PLCs will read the physical state of the system from the DB
2. Exchange sensor information, locally and remotely (using network messages)
3. Execute control actions
4. Write the actuator status into the DB
5. The simulation will execute a new iteration and repeat the cycle.

Some attacks might affect this behaviour. for example, devices will overwrite the decisions taken by PLCs and network
attacks might disrupt exchanging sensor information remotely.

In addition to exchange information, the DB is used to synchronize the execution of EPANET and MiniCPS. This
synchronization was necessary in order to generate consistent physical results with DHALSIM. Before this mechanism
was present, multiple runs of the same simulation would yield slightly different results. Due to the actuators being
activated at different iterations (mostly 1 or 2 iterations). The synchronization mechanism is a semaphore mechanism
that guarantees that the steps previously discussed are executed in order. Notice that this mechanism introduces
an artifact into DHALSIM, as real systems do not have such synchronization mechanisms. Nevertheless, real systems
are designed with a computational system that runs many times faster than the physical process (and other real time
considerations). DHALSIM requires to simulate entire weeks of a system's behaviour in a few hours, so we consider that
this mechanism and tradeoff to be a reasonable one. The synchronization mechanism is present in the logic of
generic_plc, base_plc, physical_process, generic_scada, and some attacker scripts. SQLite was chosen for the
synchronization mechanism , because it was already being used by MiniCPS and its a lightweight solution. Another
approaches like using messages instead of a database were discarded, as they might generate network artifacts.


DHALSIM was designed to be a tool for WDS and other systems simulation
-----------------------------------------------------------------------
One of the earliest discussions around DHALSIM design was if it was going to represent very accurately one particular
WDS or if it was designed to be a generic tool for any WDS. We decided DHALSIM would be more useful as a generic
tool. For that reason, DHALSIM includes parsers that allow it to automatically build topologies and run experiments,
provided with the right input files. Notice that this design principle also means that DHALSIM could in the future
be extended to simulate other physical systems. The parsing and execution process of DHALSIM works like this:

1. When an experiment is launched, the main config YAML file is passed as a parameter, this file is received
   by the command_line.py script.
2. The parsers are called (config_parser and input_parser.py) to parse the different configuration files. The objective
   of these parsers is to generate an "intermediate.yaml" file. This is a master file that is used by all components
   of DHALSIM to function. At the same time, this file stores all relevant configuration information for a DHALSIM
   experiment.
3. Once the intermediate_yaml file is generated he automatic_run.py script is called. This is a process that will start
   a Mininet topology and spawn multiple subprocesses, running in Mininet nodes. There wil be one subprocess for each
   PLC present in the PLCs YAML configuration file, one subprocess for the SCADA server, one subprocess for each
   network attack, one subprocess for each router (capturing traffic with 'tcpdump') and one subprocess for the physical
   simulation. In addition, each attacker and PLC will spawn a subprocess of their own using 'tcpdump' to capture
   traffic. All subprocesses are started and finished automatically, even in the presence of execution errors.
4. The processes continue executing until the physical_process.py has run the configured number of simulation
   iterations. When this happens, this process writes the ground_truth.csv file and finishes.
5. When the physical_process finishes, all other subsubprocesses finish too, the SCADA process wil write the
   scada_values.csv file.
6. The file generator will generate a file with information about the experiment, copy all configuration information,
   results files into the output folder.

DHALSIM attack framework is lightly inspired by DETER MAGI system
-------------------------------------------------------------------

I used and studied DETER's MAGI system in 2014. Considering that DHALSIM is a tool that automatically spawns multiple
subprocesses to represent a Water Distribution System, I thought that we would need a framework that controls how
attacks are launched and stopped. We used YAML fo convenience and followed MAGI's principle that triggers would
control when an attack is launched or stopped.













