import sqlite3
import csv
import sys
import os
import pandas as pd
import yaml
import traceback
from decimal import Decimal
from datetime import datetime
from utils import T1, T2, T3, T4, T5, T6, T7, PU1, PU2, PU1F, PU2F
from utils import V2, PU3, PU4, PU5, PU6, PU7, PU8, PU9, PU10, PU11
from utils import V2F, PU3F, PU4F, PU5F, PU6F, PU7F, PU8F, PU9F, PU10F, PU11F
from utils import J280, J269, J300, J256, J289, J415, J14, J422, J302, J306, J307, J317, ATT_1, ATT_2

sys.path.insert(1, sys.path[0] + '/DHALSIM-epynet')

print(sys.path)

import network
import epynetUtils

class PhysicalPlant:

    def __init__(self):

        config_file_path = sys.argv[1]
        config_options = self.load_config(config_file_path)

        if config_options['simulation_type'] == "Batch":
            self.week_index = int(sys.argv[2])
        else:
            self.week_index = int(config_options['week_index'])

        # Some users may not configure the parameter
        # Sets the attack_flag to load attack_start and attack_end before main loop
        if config_options['run_attack']:
                if config_options['run_attack'] == "True":
                    self.attack_flag = True
                    self.attack_path = sys.argv[3]
                    self.attack_name = config_options['attack_name']
                else:
                    self.attack_flag = False
        else:
            self.attack_flag = False

        # Use of prepared statements
        self._name = 'ctown'
        self._path = config_options['db_path']
        self._value = 'value'
        self._what = ()

        self._init_what()

        if not self._what:
            raise ValueError('Primary key not found.')
        else:
            self._init_get_query()
            self._init_set_query()

        # connection to the database
        self.db_path = config_options['db_path']
        #self.conn = sqlite3.connect(self.db_path)
        #self.c = self.conn.cursor()

        self.output_path = config_options['output_ground_truth_path']
        self.simulation_days = int(config_options['duration_days'])
        print("Days: " + str(self.simulation_days))

        # Create the network
        inp_file = config_options['inp_file']
        #self.wn = wntr.network.WaterNetworkModel(inp_file)

        # Using Davide's epynet
        self.wn = network.WaterDistributionNetwork('ctown_map.inp')

        # todo: Check if it's better to have separate lists for tank names
        self.tank_list = list(self.wn.tanks.keys())
        self.junction_list = list(self.wn.junctions.keys())
        self.pump_list = list(self.wn.pumps.keys())
        #print("initial pump list: " + str(self.pump_list))
        self.valve_list = list(self.wn.valves.keys())

        self.scada_junction_list = ['J280', 'J269', 'J300', 'J256', 'J289', 'J415', 'J14', 'J422', 'J302', 'J306',
                                    'J307', 'J317']

        list_header = ["Timestamp"]
        list_header.extend(self.tank_list)
        list_header.extend(self.junction_list)

        aux = self.create_link_header(self.pump_list)
        list_header.extend(aux)

        aux = self.create_link_header(self.valve_list)
        list_header.extend(aux)

        list_header.extend(["Attack#01", "Attack#02"])

        #print("List header")
        #print(list_header)

        self.results_list = []
        self.results_list.append(list_header)

        self.actuator_list = None

        # intialize the simulation with the random demand patterns and tank levels
        self.initialize_simulation(config_options)

        print("Starting simulation for " + str(config_options['inp_file']) + " topology ")

    def _init_what(self):
        """Save a ordered tuple of pk field names in self._what."""

        # https://sqlite.org/pragma.html#pragma_table_info
        query = "PRAGMA table_info(%s)" % self._name
        # print "DEBUG query: ", query

        with sqlite3.connect(self._path) as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(query)
                table_info = cursor.fetchall()
                # print "DEBUG table_info: ", table_info

                # last tuple element
                pks = []
                for field in table_info:
                    if field[-1] > 0:
                        # print 'DEBUG pk field: ', field
                        pks.append(field)

                if not pks:
                    print("ERROR: please provide at least 1 primary key")
                else:
                    # sort by pk order
                    pks.sort(key=lambda x: x[5])
                    # print 'DEBUG sorted pks: ', pks

                    what_list = []
                    for pk in pks:
                        what_list.append(pk[1])
                    # print 'DEBUG what list: ', what_list

                    self._what = tuple(what_list)
                    #print('DEBUG self._what: ', self._what)

            except sqlite3.Error as e:
                print('ERROR: %s: ' % e.args[0])

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

        #print('DEBUG set_query:', set_query)
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

        #print('DEBUG get_query:', get_query)
        self._get_query = get_query

    def load_config(self, config_path):
        """
        Reads the YAML configuration file
        :param config_path: The path of the YAML configuration file
        :return: an object representing the options stored in the configuration file
        """
        with open(config_path) as config_file:
            options = yaml.load(config_file, Loader=yaml.FullLoader)
        return options

    def configure_demand_patterns(self, patterns_path, starting_demand):
        limit = (self.simulation_days * 24) - 1
        total_demands = pd.read_csv(patterns_path)
        demand_starting_points = pd.read_csv(starting_demand, index_col=0)

        week_start = demand_starting_points.iloc[self.week_index][0]
        week_demands = total_demands.loc[week_start:week_start + limit, :]

        for pattern in self.wn.patterns.uid:
            self.wn.set_demand_pattern(pattern, week_demands[pattern].values.tolist())

    def configure_initial_tank_levels(self, tank_levels_path):
        initial_tank_levels = pd.read_csv(tank_levels_path, index_col=0)
        #todo: Handle exception if there are key errors due to malformed columns in the tank init file
        for tank in initial_tank_levels.columns:
            self.wn.tanks[tank].tanklevel = float(initial_tank_levels.iloc[self.week_index][tank])

    def initialize_simulation(self, config_options):
        self.build_initial_actuator_dict()

        if 'initial_custom_flag' in config_options:
            if config_options['initial_custom_flag'] == "True":
                demand_patterns_path = config_options['demand_patterns_path']
                starting_demand_path = config_options['starting_demand_path']
                print("Running simulation with demmand patterns of week: " + str(self.week_index))
                self.configure_demand_patterns(demand_patterns_path, starting_demand_path)

                initial_tank_levels_path = config_options['initial_tank_levels_path']
                self.configure_initial_tank_levels(initial_tank_levels_path)

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
                print('Invalid actuator!')

        self.actuator_list = dict(zip(actuator_names, actuator_status))
        #print("Initial actuator state: " + str(self.actuator_list))

    def create_link_header(self, a_list):
        result = []
        for link in a_list:
            result.append(link + "_FLOW")
            result.append(link + "_STATUS")
        return result

    def get_actuator_status(self, actuator):
        return int(self.get_from_db(actuator))

    def update_actuators(self):
        for actuator in self.actuator_list:
            self.actuator_list[actuator] = self.get_actuator_status(actuator)

    def register_results(self, results):

        values_list = []
        values_list.extend([datetime.now()])

        for tank in self.tank_list:
            #print(str(tank) + " Tank Pressure: " + str(results[tank]['pressure']))
            values_list.extend([results[tank]['pressure']])

        # Get junction  levels
        for junction in self.junction_list:
            #print(str(junction) + " Junction Pressure: " + str(self.wn.junctions[junction].pressure.iloc[-1]))
            values_list.extend([self.wn.junctions[junction].pressure.iloc[-1]])

        # toDo: For some reason, pump_list now also includes the valves
        for pump in self.pump_list:
            values_list.extend([results[pump]['flow'], results[pump]['status']])

        attack1 = 0
        attack2 = 0

        try:
            attack1 = int(self.get_from_db('ATT_1'))
            attack2 = int(self.get_from_db('ATT_2'))
        except Exception:
            print("Warning DB locked")

        values_list.extend([attack1, attack2])
        return values_list

    def write_results(self, results):
        with open('output/' + self.output_path, 'w') as f:
            print("Saving output to: " + 'output/' + self.output_path)
            writer = csv.writer(f)
            writer.writerows(results)

    def load_attack_options(self):
        with open(self.attack_path) as config_file:
            attack_file = yaml.load(config_file, Loader=yaml.FullLoader)

        for attack in attack_file['attacks']:
            if self.attack_name == attack['name']:
                self.attack_start = int(attack['start'])
                self.attack_end = int(attack['end'])
                self.attack_type = attack['type']

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

        with sqlite3.connect(self._path) as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(self._set_query, what)
                conn.commit()
                return value

            except sqlite3.Error as e:
                print('_set ERROR: %s: ' % e.args[0])

    def get_from_db(self, what):
        """Returns the first element of the result tuple."""
        what_tuple = self.convert_to_tuple(what)
        with sqlite3.connect(self.db_path) as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(self._get_query, what_tuple)
                record = cursor.fetchone()
                return record[0]

            except sqlite3.Error as e:
                print('_get ERROR: %s: ' % e.args[0])

    def main(self):

        # toDO: These parameters need to be imported form the yaml file
        simluation_step = 300
        simulation_duration = self.simulation_days * 24 * 3600

        self.wn.set_time_params(duration=simulation_duration, hydraulic_step=simluation_step)
        self.wn.init_simulation(interactive=True)

        master_time = 0
        iteration_limit = simulation_duration / simluation_step

        # check attack duration
        if self.attack_flag:
            self.load_attack_options()
            print("Launching attack " + str(self.attack_name) + " with start in iteration " + str(self.attack_start)
                  + " and finish at iteration " + str(self.attack_end))
        else:
            self.attack_start = 0
            self.attack_end = 0

        if iteration_limit >= self.attack_start:
            print("Warning. Attack starts at or after iteration limit")

        print("Simulation will run for " + str(self.simulation_days) + " days. Hydraulic timestep is " + str(
            simluation_step) +
              " for a total of " + str(iteration_limit) + " iterations ")

        print("Output path will be: " + str(self.output_path))

        internal_epynet_step = 1
        simulation_time = 0

        while internal_epynet_step > 0:

            self.update_actuators()

            try:
                internal_epynet_step, network_state = self.wn.simulate_step(simulation_time, self.actuator_list)
            except IndexError as i_error:
                print("ERROR: ", i_error)
                traceback.print_exc()
                break

            if internal_epynet_step == simluation_step:
                master_time += 1

            print("Internal epynet step: " + str(internal_epynet_step))
            print("ITERATION %d ------------- " % master_time)

            step_results = self.register_results(network_state)

            self.results_list.append(step_results)

            simulation_time = simulation_time + internal_epynet_step

            try:
                # Update tank pressure
                for tank in self.tank_list:
                    a_level = network_state[tank]['pressure']
                    self.set_to_db(tank, a_level)

                # Update pump flow
                for pump in self.pump_list:
                    a_flowrate = network_state[pump]['flow']
                    pump_name = pump + 'F'
                    self.set_to_db(pump_name, a_flowrate)

                # Update valve flow
                for valve in self.valve_list:
                    a_flowrate = network_state[valve]['flow']
                    valve_name = valve + 'F'
                    self.set_to_db(valve_name, a_flowrate)

                # Update the SCADA junctions
                #print(self.scada_junction_list)
                for junction in self.scada_junction_list:
                    junction_name = junction
                    a_level = self.wn.junctions[junction].pressure.iloc[-1]
                    self.set_to_db(junction_name, a_level)

                self.set_to_db('CONTROL', 0)

                # For concealment attacks, we need more stages in the attack
                if self.attack_flag and (self.attack_type == "device_attack" or self.attack_type == "network_attack"):
                    if self.attack_start <= master_time < self.attack_end:
                        self.set_to_db('ATT_2', 1)
                    else:
                        self.set_to_db('ATT_2', 0)

            except sqlite3 as ex:
                print("Warning, DB error")
                print(ex)
                continue

        self.write_results(self.results_list)

if __name__ == "__main__":
    simulation = PhysicalPlant()
    simulation.main()