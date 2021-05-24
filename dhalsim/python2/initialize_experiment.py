import yaml
import sys
import subprocess
from os.path import expanduser
from py2_logger import get_logger


class ExperimentInitializer:

    def __init__(self, config_file_path, week_index):

        with open(config_file_path) as config_file:
            self.options = yaml.load(config_file, Loader=yaml.FullLoader)

        self.logger = get_logger(self.intermediate_yaml['log_level'])

        # Simulation type is needed to handle week_index.
        if 'simulation_type' in self.options:
            self.simulation_type = self.options['simulation_type']
        else:
            self.simulation_type = 'Single'

        if self.simulation_type == 'Batch':
            if 'initial_custom_flag' in self.options and 'demand_patterns_path' in self.options and 'starting_demand_path' \
                    and 'initial_tank_levels_path' in self.options:
                self.week_index = week_index
            else:
                self.logger.critical("Batch mode configured, but no initial customization options are set, aborting.")
                sys.exit(1)
        elif self.simulation_type == "Single":
            try:
                self.week_index = int(self.options['week_index'])
            except KeyError:
                self.logger.info("Missing week index parameter in yaml configuration file.")

        else:
            self.logger.critical("Invalid simulation mode, supported values are 'Single' and 'Batch', aborting.")
            sys.exit(1)

        # complex_topology flag is going to define which topo instance we create
        if 'complex_topology' in self.options:
            if self.options['complex_topology'] == 'True':
                self.complex_topology = True
            elif self.options['complex_topology'] == 'False':
                self.complex_topology = False
            else:
                self.logger.critical("Complex_topology parameter has to be a boolean, aborting.")
                sys.exit(1)
        else:
            self.complex_topology = False

        # Parse the EPANET and epanetCPA files to get the number of PLCs and the PLC dependencies
        # Number of PLCs is needed to build the network topologies. PLC dependencies are needed to infer launch order

        # Default launches enhanced ctown
        if 'epanet_topo_path' in self.options:
            self.epanet_file_path = self.options['epanet_topo_path']
        else:
            self.epanet_file_path = '../../Demand_patterns/ctown_map_with_controls.inp'

        if 'epanet_cpa_path' in self.options:
            self.cpa_file_path = self.options['epanet_cpa_path']
        else:
            self.cpa_file_path = '../../Demand_patterns/ctown.cpa'

        if 'plc_dict_path' in self.options:
            self.plc_dict_path = self.options['plc_dict_path']
        else:
            self.plc_dict_path = 'plc_dicts.yaml'

        if 'run_attack' in self.options:
            if self.options['run_attack'] == 'True':
                self.run_attack = True

                if 'attacks_path' in self.options:
                    self.attack_path = self.options['attacks_path']
                else:
                    self.logger.warning("Warning. Using default attack path ../../attack_repository/ctown.cpa.")
                    self.attack_path = '../../attack_repository/attack_description.yaml'

                if 'attack_name' in self.options:
                    self.attack_name = self.options['attack_name']
                else:
                    self.logger.warning("Warning. Using default attack plc_empty_tank_1.")
                    self.attack_name = 'plc_empty_tank_1'
            else:
                self.run_attack = False
        else:
            self.run_attack = False

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

    def get_attack_flag(self):
        return self.run_attack

    def get_attack_path(self):
        return self.attack_path

    def get_attack_name(self):
        return self.attack_name

    def run_parser(self):
        """
        Parse the files to build plc_dicts.yaml and utils.py.

        :return:
        """
        home_path = expanduser("~")
        wntr_environment_path = home_path + str('/wntr-experiments/bin/python')
        parse_process = subprocess.call(
            [wntr_environment_path, 'epanet_parser.py', '-i', self.epanet_file_path, '-a', self.cpa_file_path, '-o',
             'plc_dicts.yaml'])
