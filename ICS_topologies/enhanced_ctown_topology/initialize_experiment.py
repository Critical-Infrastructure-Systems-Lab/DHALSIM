import yaml
import sys
import subprocess
from os.path import expanduser

class ExperimentInitializer:

    def __init__(self, config_file_path, week_index):

        with open(config_file_path) as config_file:
            self.options = yaml.load(config_file, Loader=yaml.FullLoader)

        # Simulation type is needed to handle week_index.
        if 'simulation_type' in self.options:
            self.simulation_type = self.options['simulation_type']
        else:
            self.simulation_type = "Single"

        if self.simulation_type == "Batch":
            print "Running Batch simulation"
            if 'initial_custom_flag' in self.options and 'demand_patterns_path' in self.options and 'starting_demand_path' \
                    and 'initial_tank_levels_path' in self.options:
                self.week_index = week_index
            else:
                print 'Batch mode configured, but no initial customization options are set, aborting.'
                sys.exit(1)
        elif self.simulation_type == "Single":
            print "Running Single simulation"
            self.week_index = int(self.options['week_index'])
        else:
            print 'Invalid simulation mode, supported values are "Single" and "Batch", aborting'
            sys.exit(1)

        # complex_topology flag is going to define which topo instance we create
        if 'complex_topology' in self.options:
            if self.options['complex_topology'] == "True":
                self.complex_topology = True
            elif self.options['complex_topology'] == "False":
                self.complex_topology = False
            else:
                print 'complex_topology parameter has to bee a bolean, aborting'
                sys.exit(1)
        else:
            self.complex_topology = False

        # Parse the EPANET and epanetCPA files to get the number of PLCs and the PLC dependencies
        # Number of PLCs is needed to build the network topologies. PLC dependencies are needed to infer launch order

        # Default launches enhanced ctown
        if 'epanet_topo_path' in self.options:
            self.epanet_file_path = self.options['epanet_topo_path']
        else:
            self.epanet_file_path = "../../Demand_patterns/ctown_map_with_controls.inp"

        if 'epanet_cpa_path' in self.options:
            self.cpa_file_path = self.options['epanet_cpa_path']
        else:
            self.cpa_file_path = "../../Demand_patterns/ctown.cpa"

        if 'plc_dict_path' in self.options:
            self.plc_dict_path = self.options['plc_dict_path']
        else:
            self.plc_dict_path = "plc_dicts.yaml"

    def get_plc_dict_path(self):
        return self.plc_dict_path

    def get_week_index(self):
        return self.week_index

    def get_simulation_type(self):
        return self.simulation_type

    def get_complex_topology(self):
        return self.complex_topology

    def get_epanet_file_path(self):
        return self.epanet_file_path

    def get_cpa_file_path(self):
        return self.cpa_file_path

    def run_parser(self):
        """
        Parse the files to build plc_dicts.yaml and utils.py
        :return:
        """
        home_path = expanduser("~")
        wntr_environment_path = home_path + str("/wntr-experiments/bin/python")
        parse_process = subprocess.call([wntr_environment_path, 'epanet_parser.py', '-i', self.epanet_file_path, '-a', self.cpa_file_path, '-o', 'plc_dicts.yaml'])