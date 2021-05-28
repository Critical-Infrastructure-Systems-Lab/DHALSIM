import argparse
import csv
import os
import signal
import logging
from decimal import Decimal

import pandas as pd
import progressbar
import wntr
import wntr.network.controls as controls
import sqlite3
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from dhalsim.py3_logger import get_logger

import wntr
import wntr.network.controls as controls
import yaml


class PhysicalPlant:

    def __init__(self, intermediate_yaml):
        logging.getLogger('wntr').setLevel(logging.WARNING)

        signal.signal(signal.SIGINT, self.interrupt)
        signal.signal(signal.SIGTERM, self.interrupt)

        self.intermediate_yaml = intermediate_yaml

        with self.intermediate_yaml.open(mode='r') as file:
            self.data = yaml.safe_load(file)

        self.logger = get_logger(self.data['log_level'])

        try:
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
            self.pump_list = self.get_link_list_by_type(self.link_list, 'Pump')
            self.valve_list = self.get_link_list_by_type(self.link_list, 'Valve')

            list_header = ["Timestamps"]

            list_header.extend(self.create_node_header(self.tank_list))
            list_header.extend(self.create_node_header(self.junction_list))
            list_header.extend(self.create_link_header(self.pump_list))
            list_header.extend(self.create_link_header(self.valve_list))

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

            simulator_string = self.data['simulator']

            if simulator_string == 'pdd':
                self.logger.info("Running simulation using PDD.")
                self.wn.options.hydraulic.demand_model = 'PDD'
            elif simulator_string == 'dd':
                self.logger.info("Running simulation using DD.")
            else:
                self.logger.critical('Invalid simulation mode, exiting.')
                sys.exit(1)

            # Set initial physical conditions
            self.set_initial_values()

            self.sim = wntr.sim.WNTRSimulator(self.wn)

            self.logger.info("Starting simulation for " + str(self.data['inp_file']) + " topology.")
        except KeyError as e:
            self.logger.critical("An incorrect YAML file has been supplied: " + str(e))
            sys.exit(1)

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

    def register_results(self, results):
        values_list = []
        values_list.extend([results.timestamp])

        # Results are divided into: nodes: reservoir and tanks, links: flows and status
        # Get tanks levels
        for tank in self.tank_list:
            values_list.extend([self.wn.get_node(tank).level])

        # Get junction  levels
        for junction in self.junction_list:
            values_list.extend(
                [self.wn.get_node(junction).head - self.wn.get_node(junction).elevation])

        # Get pumps flows and status
        for pump in self.pump_list:

            values_list.extend([self.wn.get_link(pump).flow])

            if type(self.wn.get_link(pump).status) is int:
                values_list.extend([self.wn.get_link(pump).status])
            else:
                values_list.extend([self.wn.get_link(pump).status.value])

                # Get valves flows and status
        for valve in self.valve_list:
            values_list.extend([self.wn.get_link(valve).flow])

            if type(self.wn.get_link(valve).status) is int:
                values_list.extend([self.wn.get_link(valve).status])
            else:
                values_list.extend([self.wn.get_link(valve).status.value])

        return values_list

    def update_controls(self):
        for control in self.control_list:
            self.update_control(control)

    def update_control(self, control):
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
        with self.ground_truth_path.open(mode='w') as f:
            writer = csv.writer(f)
            writer.writerows(results)

    def get_plcs_ready(self):
        self.c.execute("""SELECT count(*)
                        FROM sync
                        WHERE flag <= 0""")
        flag = int(self.c.fetchone()[0]) == 0
        return flag

    def main(self):
        # We want to simulate only 1 hydraulic timestep each time MiniCPS processes the simulation data
        self.wn.options.time.duration = self.wn.options.time.hydraulic_timestep

        master_time = -1

        iteration_limit = self.data["iterations"]

        self.logger.info("Simulation will run for {x} iterations.".format(x=str(iteration_limit)))
        self.logger.info("Hydraulic timestep is {timestep}.".format(
            timestep=str(self.wn.options.time.hydraulic_timestep)))

        if self.data['log_level'] is not 'debug':
            widgets = [' [', progressbar.Timer(), ' - ', progressbar.SimpleProgress(), '] ',
                       progressbar.Bar(), ' [', progressbar.ETA(), '] ', ]
            p_bar = progressbar.ProgressBar(max_value=iteration_limit, widgets=widgets)
            p_bar.start()

        while master_time < iteration_limit:
            self.c.execute("REPLACE INTO master_time (id, time) VALUES(1, ?)", (str(master_time),))
            self.conn.commit()

            # Increment master time
            master_time = master_time + 1

            while not self.get_plcs_ready():
                time.sleep(0.01)

            self.update_controls()

            self.logger.debug("Iteration %d out of %d." % (master_time, iteration_limit))
            if self.data['log_level'] is not 'debug':
                p_bar.update(master_time)

            results = self.sim.run_sim(convergence_error=True)
            values_list = self.register_results(results)
            self.results_list.append(values_list)

            # Update tanks in database
            for tank in self.tank_list:
                a_level = self.wn.get_node(tank).level
                self.c.execute("UPDATE plant SET value = ? WHERE name = ?",
                               (str(a_level), tank,))
                self.conn.commit()

            # Update pumps in database
            for pump in self.pump_list:
                flow = Decimal(self.wn.get_link(pump).flow)
                self.c.execute("UPDATE plant SET value = ? WHERE name = ?",
                               (str(flow), pump+"F",))
                self.conn.commit()

            # Update valve in database
            for valve in self.valve_list:
                flow = Decimal(self.wn.get_link(valve).flow)
                self.c.execute("UPDATE plant SET value = ? WHERE name = ?",
                               (str(flow), valve+"F",))
                self.conn.commit()

            # Update junction pressure:
            for junction in self.junction_list:
                level = Decimal(self.wn.get_node(junction).head - self.wn.get_node(junction).elevation)
                # pressure = Decimal(self.wn.get_node(junction).pressure)
                self.c.execute("UPDATE plant SET value = ? WHERE name = ?",
                               (str(level), junction,))
                self.conn.commit()

            # Set sync flags for nodes
            self.c.execute("UPDATE sync SET flag=0")
            self.conn.commit()

        self.finish()

    def interrupt(self, sig, frame):
        self.finish()
        self.logger.info("Simulation ended.")
        sys.exit(0)

    def finish(self):
        self.write_results(self.results_list)
        self.logger.info("Simulation finished.")
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
