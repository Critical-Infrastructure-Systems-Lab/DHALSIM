import argparse
import csv
import os
import signal
import logging
from datetime import datetime
from decimal import Decimal

import pandas as pd
import progressbar
import sqlite3
import sys
import time
from pathlib import Path

from dhalsim.parser.file_generator import BatchReadmeGenerator, GeneralReadmeGenerator
from dhalsim.py3_logger import get_logger
import wntr
import wntr.network.controls as controls
import yaml


class PhysicalPlant:
    """
    Class representing the plant itself, runs each iteration. This class also deals with WNTR
    and updates the database.
    """

    def __init__(self, intermediate_yaml):
        signal.signal(signal.SIGINT, self.interrupt)
        signal.signal(signal.SIGTERM, self.interrupt)

        self.intermediate_yaml = intermediate_yaml

        with self.intermediate_yaml.open(mode='r') as file:
            self.data = yaml.safe_load(file)

        logging.getLogger('wntr').setLevel(logging.WARNING)
        self.logger = get_logger(self.data['log_level'])

        self.ground_truth_path = Path(self.data["output_path"]) / "ground_truth.csv"
        self.ground_truth_path.touch(exist_ok=True)

        # connection to the database
        self.conn = sqlite3.connect(self.data["db_path"])
        self.c = self.conn.cursor()

        # Create the network
        self.wn = wntr.network.WaterNetworkModel(self.data['inp_file'])

        self.node_list = list(self.wn.node_name_list)
        self.link_list = list(self.wn.link_name_list)

        self.tank_list = self.get_node_list_by_type(self.node_list, 'Tank')
        self.junction_list = self.get_node_list_by_type(self.node_list, 'Junction')

        self.scada_junction_list = self.get_scada_junction_list(self.data['plcs'])

        self.pump_list = self.get_link_list_by_type(self.link_list, 'Pump')
        self.valve_list = self.get_link_list_by_type(self.link_list, 'Valve')
        self.values_list = list()

        list_header = ['iteration', 'timestamp']
        list_header.extend(self.create_node_header(self.tank_list))
        list_header.extend(self.create_node_header(self.junction_list))
        list_header.extend(self.create_link_header(self.pump_list))
        list_header.extend(self.create_link_header(self.valve_list))

        list_header.extend(self.create_attack_header())

        self.results_list = []
        self.results_list.append(list_header)

        dummy_condition = controls.ValueCondition(self.wn.get_node(self.tank_list[0]), 'level',
                                                  '>=', -1)

        self.control_list = []
        for valve in self.valve_list:
            self.control_list.append(self.create_control_dict(valve, dummy_condition))

        for pump in self.pump_list:
            self.control_list.append(self.create_control_dict(pump, dummy_condition))

        for control in self.control_list:
            an_action = controls.ControlAction(control['actuator'], control['parameter'],
                                               control['value'])
            a_control = controls.Control(control['condition'], an_action, name=control['name'])
            self.wn.add_control(control['name'], a_control)

        if self.data['simulator'] == 'pdd':
            self.wn.options.hydraulic.demand_model = 'PDD'

        # Set initial physical conditions
        self.set_initial_values()

        self.sim = wntr.sim.WNTRSimulator(self.wn)

        self.logger.info("Starting simulation for " +
                         os.path.basename(str(self.data['inp_file']))[:-4] + " topology.")

        self.start_time = datetime.now()
        self.master_time = -1
        self.db_update_string = "UPDATE plant SET value = ? WHERE name = ?"

    def get_scada_junction_list(self, plcs):

        junction_list = []

        for PLC in plcs:
            if 'sensors' not in PLC:
                PLC['sensors'] = list()

            for sensor in PLC['sensors']:
                if sensor != "" and sensor in self.junction_list:
                    junction_list.append(sensor)

        return junction_list

    def get_node_list_by_type(self, a_list, a_type):
        result = []
        for node in a_list:
            if self.wn.get_node(node).node_type == a_type:
                result.append(str(node))
        return result

    def get_link_list_by_type(self, a_list, a_type):
        result = []
        for link in a_list:
            if self.wn.get_link(link).link_type == a_type:
                result.append(str(link))
        return result

    @staticmethod
    def create_node_header(a_list):
        result = []
        for node in a_list:
            result.append(node + "_LEVEL")
        return result

    @staticmethod
    def create_link_header(a_list):
        result = []
        for link in a_list:
            result.append(link + "_FLOW")
            result.append(link + "_STATUS")
        return result

    def create_attack_header(self):
        """
        Function that creates csv list headers for device and network attacks

        :return: list of attack names starting with device and ending with network
        """
        result = []
        # Append device attacks
        if "plcs" in self.data:
            for plc in self.data["plcs"]:
                if "attacks" in plc:
                    for attack in plc["attacks"]:
                        result.append(attack['name'])
        # Append network attacks
        if "network_attacks" in self.data:
            for network_attack in self.data["network_attacks"]:
                result.append(network_attack['name'])

        return result

    def get_controls(self, a_list):
        result = []
        for control in a_list:
            result.append(self.wn.get_control(control))
        return result

    def create_control_dict(self, actuator, dummy_condition):
        act_dict = dict.fromkeys(['actuator', 'parameter', 'value', 'condition', 'name'])
        act_dict['actuator'] = self.wn.get_link(actuator)
        act_dict['parameter'] = 'status'
        act_dict['condition'] = dummy_condition
        act_dict['name'] = actuator
        if type(self.wn.get_link(actuator).status) is int:
            act_dict['value'] = act_dict['actuator'].status
        else:
            act_dict['value'] = act_dict['actuator'].status.value
        return act_dict

    def register_results(self):
        # Results are divided into: nodes: reservoir and tanks, links: flows and status
        self.values_list = [self.master_time, datetime.now()]
        self.extend_tanks()
        self.extend_junctions()
        self.extend_pumps()
        self.extend_valves()
        self.extend_attacks()

    def extend_tanks(self):
        # Get tanks levels
        for tank in self.tank_list:
            self.values_list.extend([self.wn.get_node(tank).level])

    def extend_junctions(self):
        # Get junction  levels
        for junction in self.junction_list:
            self.values_list.extend(
                [self.wn.get_node(junction).head - self.wn.get_node(junction).elevation])

    def extend_pumps(self):
        # Get pumps flows and status
        for pump in self.pump_list:

            self.values_list.extend([self.wn.get_link(pump).flow])

            if type(self.wn.get_link(pump).status) is int:
                self.values_list.extend([self.wn.get_link(pump).status])
            else:
                self.values_list.extend([self.wn.get_link(pump).status.value])

    def extend_valves(self):
        # Get valves flows and status
        for valve in self.valve_list:
            self.values_list.extend([self.wn.get_link(valve).flow])

            if type(self.wn.get_link(valve).status) is int:
                self.values_list.extend([self.wn.get_link(valve).status])
            else:
                self.values_list.extend([self.wn.get_link(valve).status.value])

    def extend_attacks(self):
        # Get device attacks
        if "plcs" in self.data:
            for plc in self.data["plcs"]:
                if "attacks" in plc:
                    for attack in plc["attacks"]:
                        self.values_list.append(self.get_attack_flag(attack['name']))
        # get network attacks
        if "network_attacks" in self.data:
            for network_attack in self.data["network_attacks"]:
                self.values_list.append(self.get_attack_flag(network_attack['name']))

    def update_controls(self):
        """Updates all controls in WNTR."""
        for control in self.control_list:
            rows_1 = self.c.execute('SELECT value FROM plant WHERE name = ?',
                                    (control['name'],)).fetchone()
            self.conn.commit()
            new_status = int(rows_1[0])

            control['value'] = new_status

            new_action = controls.ControlAction(control['actuator'], control['parameter'],
                                                control['value'])
            new_control = controls.Control(control['condition'], new_action, name=control['name'])

            self.wn.remove_control(control['name'])
            self.wn.add_control(control['name'], new_control)

    def write_results(self, results):
        """Writes ground truth file."""
        with self.ground_truth_path.open(mode='w') as f:
            writer = csv.writer(f)
            writer.writerows(results)

    def get_plcs_ready(self):
        """
        Checks whether all PLCs have finished their loop.
        :return: boolean whether all PLCs have finished
        """
        self.c.execute("""SELECT count(*)
                        FROM sync
                        WHERE flag <= 0""")
        flag = int(self.c.fetchone()[0]) == 0
        return flag

    def get_attack_flag(self, name):
        """
        Get the attack flag of this attack.

        :return: False if attack not running, true otherwise
        """
        self.c.execute("SELECT flag FROM attack WHERE name IS ?", (name,))
        flag = int(self.c.fetchone()[0])
        return flag

    def main(self):
        """Runs the simulation for x iterations."""

        # We want to simulate only one hydraulic timestep each time MiniCPS processes the
        # simulation data
        self.wn.options.time.duration = self.wn.options.time.hydraulic_timestep

        iteration_limit = self.data["iterations"]

        self.logger.debug("Temporary file location: " + str(Path(self.data["db_path"]).parent))

        if 'batch_index' in self.data:
            self.logger.info("Running batch simulation {x} out of {y}."
                             .format(x=self.data['batch_index'] + 1,
                                     y=self.data['batch_simulations']))

        self.logger.info("Simulation will run for {x} iterations with hydraulic timestep {step}."
                         .format(x=str(iteration_limit),
                                 step=str(self.wn.options.time.hydraulic_timestep)))

        p_bar = None
        if self.data['log_level'] != 'debug':
            widgets = [' [', progressbar.Timer(), ' - ', progressbar.SimpleProgress(), '] ',
                       progressbar.Bar(), ' [', progressbar.ETA(), '] ', ]
            p_bar = progressbar.ProgressBar(max_value=iteration_limit, widgets=widgets)
            p_bar.start()

        while self.master_time < iteration_limit:
            self.c.execute("REPLACE INTO master_time (id, time) VALUES(1, ?)", (str(self.master_time),))
            self.conn.commit()

            self.master_time = self.master_time + 1

            while not self.get_plcs_ready():
                time.sleep(0.01)

            self.update_controls()

            self.logger.debug("Iteration {x} out of {y}.".format(x=str(self.master_time),
                                                                 y=str(iteration_limit)))

            if p_bar:
                p_bar.update(self.master_time)

            # Check for simulation error, print output on exception
            try:
                self.sim.run_sim(convergence_error=True)
            except Exception as exp:
                self.logger.error(f"Error in WNTR simulation: {exp}")
                self.finish()

            self.register_results()
            self.results_list.append(self.values_list)

            self.update_tanks()
            self.update_pumps()
            self.update_valves()
            self.update_junctions()

            # Write results of this iteration if needed
            if 'saving_interval' in self.data and self.master_time != 0 and \
                    self.master_time % self.data['saving_interval'] == 0:
                self.write_results(self.results_list)

            # Set sync flags for nodes
            self.c.execute("UPDATE sync SET flag=0")
            self.conn.commit()

        self.finish()

    def update_tanks(self):
        """Update tanks in database."""
        for tank in self.tank_list:
            a_level = self.wn.get_node(tank).level
            self.c.execute(self.db_update_string, (str(a_level), tank,))
            self.conn.commit()

    def update_pumps(self):
        """"Update pumps in database."""
        for pump in self.pump_list:
            flow = Decimal(self.wn.get_link(pump).flow)
            self.c.execute(self.db_update_string, (str(flow), pump + "F",))
            self.conn.commit()

    def update_valves(self):
        """Update valve in database."""
        for valve in self.valve_list:
            flow = Decimal(self.wn.get_link(valve).flow)
            self.c.execute(self.db_update_string, (str(flow), valve + "F",))
            self.conn.commit()

    def update_junctions(self):
        """Update junction pressure in database."""

        # todo: Test this
        # for junction in self.junction_list:
        for junction in self.scada_junction_list:

            level = Decimal(self.wn.get_node(junction).head - self.wn.get_node(junction).elevation)
            self.c.execute(self.db_update_string, (str(level), junction,))
            self.conn.commit()

    def interrupt(self, sig, frame):
        self.finish()
        self.logger.info("Simulation ended.")
        sys.exit(0)

    def finish(self):
        self.write_results(self.results_list)
        end_time = datetime.now()

        if 'batch_simulations' in self.data:
            readme_path = Path(self.data['config_path']).parent / self.data['output_path']\
                          / 'configuration' / 'batch_readme.md'
            os.makedirs(str(readme_path.parent), exist_ok=True)

            BatchReadmeGenerator(self.intermediate_yaml, readme_path, self.start_time, end_time,
                                 self.wn, self.master_time).write_batch()
            if self.data['batch_index'] == self.data['batch_simulations'] - 1:
                GeneralReadmeGenerator(self.intermediate_yaml, self.data['start_time'],
                                       end_time, True, self.master_time, self.wn).write_readme()
        else:
            GeneralReadmeGenerator(self.intermediate_yaml, self.data['start_time'],
                                   end_time, False, self.master_time, self.wn).write_readme()
        sys.exit(0)

    def set_initial_values(self):
        """Sets custom initial values for tanks and demand patterns in the WNTR simulation"""

        if "initial_tank_values" in self.data:
            # Initial tank values
            for tank in self.tank_list:
                if str(tank) in self.data["initial_tank_values"]:
                    value = self.data["initial_tank_values"][str(tank)]
                    self.logger.debug("Setting tank " + tank + " initial value to " + str(value))
                    self.wn.get_node(tank).init_level = value
                else:
                    self.logger.debug("Tank " + tank + " has no specified initial values, using default...")

        if "demand_patterns_data" in self.data:
            # Demand patterns for batch
            demands = pd.read_csv(self.data["demand_patterns_data"])
            for name, pat in self.wn.patterns():
                if name in demands:
                    self.logger.debug("Setting demands for " + name +
                                      " to demands defined at: " + self.data["demand_patterns_data"])
                    pat.multipliers = demands[name].values.tolist()
                else:
                    self.logger.debug("Consumer " + name + " has no demands defined, using default...")


def is_valid_file(test_parser, arg):
    if not os.path.exists(arg):
        test_parser.error(arg + " does not exist.")
    else:
        return arg


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the simulation')
    parser.add_argument(dest="intermediate_yaml",
                        help="intermediate yaml file", metavar="FILE",
                        type=lambda x: is_valid_file(parser, x))

    args = parser.parse_args()

    simulation = PhysicalPlant(Path(args.intermediate_yaml))
    simulation.main()
