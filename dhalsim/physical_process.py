import argparse
import csv
import os
import signal
import logging
from datetime import datetime
import random

import pandas as pd
import progressbar
import sqlite3
import sys
import time
from pathlib import Path

from dhalsim.parser.file_generator import BatchReadmeGenerator, GeneralReadmeGenerator
from dhalsim.py3_logger import get_logger
import yaml

from epynet.network import WaterDistributionNetwork
from epynet import epynetUtils


class Error(Exception):
    """Base class for exceptions in this module."""


class DatabaseError(Error):
    """Raised when not being able to connect to the database"""


class PhysicalPlant:
    """
    Class representing the plant itself, runs each iteration. This class also deals with WNTR
    and updates the database.
    """

    DB_TRIES = 10
    """Amount of times a db query will retry on a exception"""

    DB_SLEEP_TIME = random.uniform(0.01, 0.1)
    """Amount of time a db query will wait before retrying"""

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

        # Use of prepared statements
        self._name = 'plant'
        self._path = self.data["db_path"]
        self._value = 'value'
        self._what = ()

        self._init_what()

        if not self._what:
            raise ValueError('Primary key not found.')
        else:
            self._init_get_query()
            self._init_set_query()

        # connection to the database
        self.db_path = self.data["db_path"]

        # epynet
        original_inp_filename = self.data['inp_file'].rsplit('.', 1)[0]
        processed_inp_filename = original_inp_filename+'_processed.inp'

        try:
            self.remove_controls_from_inp_file(self.data['inp_file'], processed_inp_filename)
        except IOError as ioe:
            self.logger.error('IO Exception writing an EPANET file without [CONTROLS], aborting')
            sys.exit(1)

        # using an epynet water network object we do not have a way of removing the controls, so we write a new
        # EPANET inp file without the [CONTROLS] section
        self.wn = WaterDistributionNetwork(processed_inp_filename)

        # epynet
        self.simulation_step = epynetUtils.get_time_parameter(
            self.wn, epynetUtils.get_time_param_code('EN_HYDSTEP'))[1]

        # epynet
        self.tank_list = list(self.wn.tanks.keys())
        self.junction_list = list(self.wn.junctions.keys())
        self.pump_list = list(self.wn.pumps.keys())
        self.valve_list = list(self.wn.valves.keys())

        self.scada_junction_list = self.get_scada_junction_list(self.data['plcs'])

        self.values_list = list()

        list_header = ['iteration', 'timestamp']
        list_header.extend(self.create_node_header(self.tank_list))
        list_header.extend(self.create_node_header(self.junction_list))
        list_header.extend(self.create_link_header(self.pump_list))
        list_header.extend(self.create_link_header(self.valve_list))

        list_header.extend(self.create_attack_header())

        self.results_list = []
        self.results_list.append(list_header)

        # epynet
        self.actuator_list = None

        # Todo: Update documentation, the demand model will now be defined in the EPANET file
        #if self.data['simulator'] == 'pdd':
        #    self.wn.options.hydraulic.demand_model = 'PDD'

        # Set initial physical conditions
        self.set_initial_values()

        # Build initial list of actuators
        self.build_initial_actuator_dict()

        self.logger.info("Starting simulation for " +
                         os.path.basename(str(self.data['inp_file']))[:-4] + " topology.")

        self.start_time = datetime.now()
        self.master_time = 0
        self.db_update_string = "UPDATE plant SET value = ? WHERE name = ?"

    # toDo: Develop a test for this method
    def remove_controls_from_inp_file(self, in_file, out_file):
        write_out = True
        with open(in_file) as infile, open(out_file, "w") as outfile:
            for line in infile:
                if write_out:
                    outfile.write(line)
                if line.startswith('[CONTROLS]'):
                    write_out = False
                    continue

                if not write_out and line.startswith('['):
                    write_out = True

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

    def build_initial_actuator_dict(self):
        actuator_status = []
        actuator_names = self.pump_list
        actuator_names.extend(self.valve_list)

        for actuator in actuator_names:
            if actuator in self.wn.pumps:
                actuator_status.append(self.wn.pumps[actuator].status)
            elif actuator in self.wn.valves:
                actuator_status.append(self.wn.valves[actuator].status)
            else:
                self.logger.error('Invalid actuator!')

        self.actuator_list = dict(zip(actuator_names, actuator_status))

    def register_results(self, results):
        # Results are divided into: nodes: reservoir and tanks, links: flows and status
        self.values_list = [self.master_time, datetime.now()]
        self.extend_tanks(results)
        self.extend_junctions(results)
        self.extend_pumps(results)

        # epynet current's version includes valves status in pumps
        #self.extend_valves(results)
        self.extend_attacks()

    def extend_tanks(self, results):
        # Get tanks levels
        for tank in self.tank_list:
            self.values_list.extend([results[tank]['pressure']])

    def extend_junctions(self, results):
        # Get junction  levels
        for junction in self.junction_list:
            self.values_list.extend(
                [self.wn.junctions[junction].pressure.iloc[-1]])

    def extend_pumps(self, results):
        # Get pumps flows and status
        for pump in self.pump_list:
            self.values_list.extend([results[pump]['flow'], results[pump]['status']])

    def extend_valves(self, results):
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

    def _init_what(self):
        """Save a ordered tuple of pk field names in self._what."""
        query = "PRAGMA table_info(%s)" % self._name

        with sqlite3.connect(self._path) as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(query)
                table_info = cursor.fetchall()

                # last tuple element
                pks = []
                for field in table_info:
                    if field[-1] > 0:
                        pks.append(field)

                if not pks:
                    self.logger.error('Please provide at least 1 primary key. Has sqlite DB been initialized?.'
                                      ' Aborting')
                    sys.exit(1)
                else:
                    # sort by pk order
                    pks.sort(key=lambda x: x[5])

                    what_list = []
                    for pk in pks:
                        what_list.append(pk[1])

                    self._what = tuple(what_list)

            except sqlite3.Error as e:
                self.logger.error('Error initializing the sqlite DB. Exiting. Error: ' + str(e))
                sys.exit(1)

    def _init_set_query(self):
        """Use prepared statements."""

        set_query = 'UPDATE %s SET %s = ? WHERE %s = ?' % (
            self._name,
            self._value,
            self._what[0])

        # for composite pk
        for pk in self._what[1:]:
            set_query += ' AND %s = ?' % (
                pk)

        self._set_query = set_query

    def _init_get_query(self):
        """Use prepared statement."""

        get_query = 'SELECT %s FROM %s WHERE %s = ?' % (
            self._value,
            self._name,
            self._what[0])

        # for composite pk
        for pk in self._what[1:]:
            get_query += ' AND %s = ?' % (
                pk)

        self._get_query = get_query

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

        #todo: Prepare query statements for this
        conn = sqlite3.connect(self.data["db_path"])
        c = conn.cursor()
        c.execute("""SELECT count(*)
                        FROM sync
                        WHERE flag <= 0""")
        flag = int(c.fetchone()[0]) == 0
        return flag

    def get_attack_flag(self, name):
        """
        Get the attack flag of this attack.

        :return: False if attack not running, true otherwise
        """
        self.c.execute("SELECT flag FROM attack WHERE name IS ?", (name,))
        flag = int(self.c.fetchone()[0])
        return flag

    def get_actuator_status(self, actuator):
        return int(self.get_from_db(actuator))

    def update_actuators(self):
        for actuator in self.actuator_list:
            self.actuator_list[actuator] = self.get_actuator_status(actuator)

    def convert_to_tuple(self, what):
        return what, 1

    def set_to_db(self, what, value):
        """Returns setted value.
        ``value``'s type is not checked, the client has to specify the correct
        one.
        what_list overwrites the given what tuple,
        eg new what tuple: ``(value, what[0], what[1], ...)``
        """
        what_list = [value]

        what_tuple = self.convert_to_tuple(what)
        for pk in what_tuple:
            what_list.append(pk)
        what = tuple(what_list)

        for i in range(self.DB_TRIES):
            with sqlite3.connect(self._path) as conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute(self._set_query, what)
                    conn.commit()
                    return value

                except sqlite3.OperationalError as e:
                    self.logger.info('Failed writing to DB')
                    time.sleep(self.DB_SLEEP_TIME)
        self.logger.error(
            "Failed to connect to db. Tried {i} times.".format(i=self.DB_TRIES))
        raise DatabaseError("Failed to get master clock from database")


    def get_from_db(self, what):
        """Returns the first element of the result tuple."""
        what_tuple = self.convert_to_tuple(what)

        for i in range(self.DB_TRIES):
            with sqlite3.connect(self.db_path) as conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute(self._get_query, what_tuple)
                    record = cursor.fetchone()
                    return record[0]

                except sqlite3.OperationalError as e:
                    self.logger.info('Failed reading to DB')
                    time.sleep(self.DB_SLEEP_TIME)
        self.logger.error(
            "Failed to connect to db. Tried {i} times.".format(i=self.DB_TRIES))
        raise DatabaseError("Failed to get master clock from database")


    def main(self):
        """Runs the simulation for x iterations."""

        iteration_limit = self.data["iterations"]
        self.logger.debug("Temporary file location: " + str(Path(self.data["db_path"]).parent))

        if 'batch_index' in self.data:
            self.logger.info("Running batch simulation {x} out of {y}."
                             .format(x=self.data['batch_index'] + 1,
                                     y=self.data['batch_simulations']))

        self.logger.info("Simulation will run for {x} iterations with hydraulic timestep {step}."
                         .format(x=str(iteration_limit),
                                 step=str(self.simulation_step)))

        p_bar = None
        if self.data['log_level'] != 'debug':
            widgets = [' [', progressbar.Timer(), ' - ', progressbar.SimpleProgress(), '] ',
                       progressbar.Bar(), ' [', progressbar.ETA(), '] ', ]
            p_bar = progressbar.ProgressBar(max_value=iteration_limit, widgets=widgets)
            p_bar.start()

        simulation_duration = iteration_limit*self.simulation_step

        self.wn.set_time_params(duration=simulation_duration, hydraulic_step=self.simulation_step)
        self.wn.init_simulation(interactive=True)

        internal_epynet_step = 1
        simulation_time = 0
        step_results = None

        while internal_epynet_step:

            conn = sqlite3.connect(self.data["db_path"])
            c = conn.cursor()
            c.execute("REPLACE INTO master_time (id, time) VALUES(1, ?)", (str(self.master_time),))
            conn.commit()

            while not self.get_plcs_ready():
                time.sleep(0.01)

            self.update_actuators()

            if p_bar:
                p_bar.update(self.master_time)

            # Check for simulation error, print output on exception
            try:
                internal_epynet_step, step_results = self.wn.simulate_step(simulation_time, self.actuator_list)
                #self.sim.run_sim(convergence_error=True)
            except Exception as exp:
                self.logger.error(f"Error in WNTR simulation: {exp}")
                self.finish()

            # epynet - we skip intermediate timesteps
            if internal_epynet_step == self.simulation_step:
                self.master_time += 1

            self.logger.debug("Iteration {x} out of {y}. Internal timestep {z}".format(x=str(self.master_time),
                                                                 y=str(iteration_limit), z=str(internal_epynet_step)))

            self.register_results(step_results)
            self.results_list.append(self.values_list)

            self.update_tanks(step_results)
            self.update_pumps(step_results)
            self.update_valves(step_results)
            self.update_junctions(step_results)

            # Write results of this iteration if needed
            if 'saving_interval' in self.data and self.master_time != 0 and \
                    self.master_time % self.data['saving_interval'] == 0:
                self.write_results(self.results_list)

            # Set sync flags for nodes
            conn = sqlite3.connect(self.data["db_path"])
            c = conn.cursor()
            c.execute("UPDATE sync SET flag=0")
            conn.commit()

            simulation_time = simulation_time + internal_epynet_step

        self.finish()

    def update_tanks(self, network_state):
        """Update tanks in database."""
        for tank in self.tank_list:
            level = network_state[tank]['pressure']
            self.set_to_db(tank, level)

    def update_pumps(self, network_state):
        """"Update pumps in database."""
        for pump in self.pump_list:
            flow = network_state[pump]['flow']
            pump_name = pump + 'F'
            self.set_to_db(pump_name, flow)

    def update_valves(self, network_state):
        """Update valve in database."""
        for valve in self.valve_list:
            flow = network_state[valve]['flow']
            valve_name = valve + 'F'
            self.set_to_db(valve_name, flow)

    def update_junctions(self, network_state):
        """Update junction pressure in database."""
        for junction in self.scada_junction_list:
            level = self.wn.junctions[junction].pressure.iloc[-1]
            self.set_to_db(junction, level)

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
                                 self.wn, self.master_time, self.simulation_step).write_batch()
            if self.data['batch_index'] == self.data['batch_simulations'] - 1:
                GeneralReadmeGenerator(self.intermediate_yaml, self.data['start_time'],
                                       end_time, True, self.master_time, self.wn, self.simulation_step).write_readme()
        else:
            GeneralReadmeGenerator(self.intermediate_yaml, self.data['start_time'],
                                   end_time, False, self.master_time, self.wn, self.simulation_step).write_readme()
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
