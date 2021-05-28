import wntr
import wntr.network.controls as controls
import sqlite3
import csv
import sys
import pandas as pd
import yaml
from decimal import Decimal

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

        # Create the network
        inp_file = config_options['inp_file']
        self.wn = wntr.network.WaterNetworkModel(inp_file)

        self.node_list = list(self.wn.node_name_list)
        self.link_list = list(self.wn.link_name_list)

        self.tank_list = self.get_node_list_by_type(self.node_list, 'Tank')
        self.junction_list = self.get_node_list_by_type(self.node_list, 'Junction')
        self.scada_junction_list = ['J280', 'J269', 'J300', 'J256', 'J289', 'J415', 'J14', 'J422', 'J302', 'J306',
                                    'J307', 'J317']

        self.pump_list = self.get_link_list_by_type(self.link_list, 'Pump')
        self.valve_list = self.get_link_list_by_type(self.link_list, 'Valve')

        list_header = ["Timestamps"]
        aux = self.create_node_header(self.tank_list)
        list_header.extend(aux)

        aux = self.create_node_header(self.junction_list)
        list_header.extend(aux)

        aux = self.create_link_header(self.pump_list)
        list_header.extend(aux)

        aux = self.create_link_header(self.valve_list)
        list_header.extend(aux)

        list_header.extend(["Attack#01", "Attack#02"])

        self.results_list = []
        self.results_list.append(list_header)

        # intialize the simulation with the random demand patterns and tank levels
        self.initialize_simulation(config_options)

        dummy_condition = controls.ValueCondition(self.wn.get_node(self.tank_list[0]), 'level', '>=', -1)

        self.control_list = []
        for valve in self.valve_list:
            self.control_list.append(self.create_control_dict(valve, dummy_condition))

        for pump in self.pump_list:
            self.control_list.append(self.create_control_dict(pump, dummy_condition))

        for control in self.control_list:
            an_action = controls.ControlAction(control['actuator'], control['parameter'], control['value'])
            a_control = controls.Control(control['condition'], an_action)
            self.wn.add_control(control['name'], a_control)

        print('controls: ' + str(self.control_list))
        simulator_string = config_options['simulator']

        if simulator_string == 'pdd':
            print('Running simulation using PDD')
            self.wn.options.hydraulic.demand_model = 'PDD'

            if self.wn.options.hydraulic.required_pressure < 0.1:
                self.wn.options.hydraulic.required_pressure = 20
                print('Warning: no required pressure specified or required pressure < minimum pressure + 0.1, setting'
                      'it to 20 (check your units); check http://wateranalytics.org/EPANET/_options_page.html')

        elif simulator_string == 'dd':
            print('Running simulation using DD')
        else:
            print('Invalid simulation mode, exiting...')
            sys.exit(1)

        self.sim = wntr.sim.WNTRSimulator(self.wn)
        #self.sim = wntr.sim.EpanetSimulator(self.wn) # This is called only once

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
                    print "ERROR: please provide at least 1 primary key"
                else:
                    # sort by pk order
                    pks.sort(key=lambda x: x[5])
                    # print 'DEBUG sorted pks: ', pks

                    what_list = []
                    for pk in pks:
                        what_list.append(pk[1])
                    # print 'DEBUG what list: ', what_list

                    self._what = tuple(what_list)
                    # print 'DEBUG self._what: ', self._what

            except sqlite3.Error, e:
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

        print 'DEBUG set_query:', set_query
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

        print 'DEBUG get_query:', get_query
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

    def initialize_simulation(self, config_options):

        limit = (self.simulation_days * 24) - 1
        if 'initial_custom_flag' in config_options:
            if config_options['initial_custom_flag'] == "True":
                demand_patterns_path = config_options['demand_patterns_path']
                starting_demand_path = config_options['starting_demand_path']
                initial_tank_levels_path = config_options['initial_tank_levels_path']

                print("Running simulation with week index: " + str(self.week_index))
                total_demands = pd.read_csv(demand_patterns_path, index_col=0)
                demand_starting_points = pd.read_csv(starting_demand_path, index_col=0)
                initial_tank_levels = pd.read_csv(initial_tank_levels_path, index_col=0)
                week_start = demand_starting_points.iloc[self.week_index][0]
                week_demands = total_demands.loc[week_start:week_start + limit, :]

                for name, pat in self.wn.patterns():
                    pat.multipliers = week_demands[name].values.tolist()

                for i in range(1, 8):
                    self.wn.get_node('T' + str(i)).init_level = \
                        float(initial_tank_levels.iloc[self.week_index]['T' + str(i)])

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

    def create_node_header(self, a_list):
        result = []
        for node in a_list:
            result.append(node + "_LEVEL")
        return result

    def create_link_header(self, a_list):
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

    def register_epanet_results(self, pressure_results, flowrate_results, status_results, timestamp):
        some_values_list = []
        some_values_list.extend([timestamp])

        # Results are divided into: nodes: reservoir and tanks, links: flows and status
        # Get tanks levels
        for tank in self.tank_list:
            some_values_list.extend([pressure_results[tank]])

        for junction in self.junction_list:
            some_values_list.extend([pressure_results[junction]])

        # Get pumps flows and status
        for pump in self.pump_list:
            some_values_list.extend([flowrate_results[pump]])
            some_values_list.extend([status_results[pump]])

        # Get valves flows and status
        for valve in self.valve_list:
            some_values_list.extend([flowrate_results[valve]])
            some_values_list.extend([status_results[valve]])

        return some_values_list

    def register_results(self, results):
        values_list = []
        values_list.extend([results.timestamp])

        # Results are divided into: nodes: reservoir and tanks, links: flows and status
        # Get tanks levels
        for tank in self.tank_list:
            values_list.extend([self.wn.get_node(tank).level])

        # Get junction  levels
        for junction in self.junction_list:
            values_list.extend([self.wn.get_node(junction).head - self.wn.get_node(junction).elevation])

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

        attack1 = 0
        attack2 = 0

        try:
            attack1 = int(self.get_from_db('ATT_1'))
            attack2 = int(self.get_from_db('ATT_2'))
        except Exception as e :
            print("Warning exception acessing DB " + str(e))

        values_list.extend([attack1, attack2])

        return values_list

    def get_actuators_state(self):

        actuator_list = []
        for valve in self.wn.valve_name_list:
            actuator_list.append(self.get_actuator_state(valve))

        for pump in self.wn.pump_name_list:
            actuator_list.append(self.get_actuator_state(pump))

        return actuator_list

    def update_controls(self):
        for control in self.control_list:
            self.update_control(control)

    def get_actuator_state(self, actuator):

        actuator_dict = {}

        act_name = '\'' + actuator + '\''
        actuator_dict['name'] = actuator
        actuator_dict['status'] = int(self.get_from_db(act_name))

        return actuator_dict

    def update_control(self, control):
        act_name = '\'' + control['name'] + '\''
        new_status = int(self.get_from_db(act_name))

        control['value'] = new_status

        new_action = controls.ControlAction(control['actuator'], control['parameter'], control['value'])
        #new_control = controls.Control(control['condition'], new_action, name=control['name'])
        new_control = controls.Control(control['condition'], new_action)

        self.wn.remove_control(control['name'])
        self.wn.add_control(control['name'], new_control)

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

    def set_to_db(self, what, value):
        """Returns setted value.
        ``value``'s type is not checked, the client has to specify the correct
        one.
        what_list overwrites the given what tuple,
        eg new what tuple: ``(value, what[0], what[1], ...)``
        """
        what_list = [value]

        for pk in what:
            what_list.append(pk)

        what = tuple(what_list)
        # print 'DEBUG set what: ', what

        with sqlite3.connect(self._path) as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(self._set_query, what)
                conn.commit()
                return value

            except sqlite3.Error, e:
                print('_set ERROR: %s: ' % e.args[0])

    def get_from_db(self, what):
        """Returns the first element of the result tuple."""

        with sqlite3.connect(self.db_path) as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(self._get_query, what)
                record = cursor.fetchone()
                return record[0]

            except sqlite3.Error, e:
                print('_get ERROR: %s: ' % e.args[0])

    def main(self):
        # We want to simulate only 1 hydraulic timestep each time MiniCPS processes the simulation data
        self.wn.options.time.duration = self.wn.options.time.hydraulic_timestep
        master_time = 0

        iteration_limit = (self.simulation_days * 24 * 3600) / self.wn.options.time.hydraulic_timestep

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
            self.wn.options.time.hydraulic_timestep) +
              " for a total of " + str(iteration_limit) + " iterations ")

        print("Output path will be: " + str(self.output_path))

        while master_time <= iteration_limit:
            self.update_controls()
            #self.update_actuators()

            #actuators_state = self.get_actuators_state()

            print("ITERATION %d ------------- " % master_time)
            results = self.sim.run_sim()
            values_list = self.register_results(results)
            #results = self.sim.run_sim()

            #results = self.sim.run_sim_with_custom_actuators(actuators_state)

            #these_pressure_results = results.node['pressure'].iloc[-1]
            #these_flowrate_results = results.link['flowrate'].iloc[-1]
            #these_status_results = results.link['status'].iloc[-1]
            #values_list = self.register_epanet_results(these_pressure_results, these_flowrate_results,
            #                                           these_status_results, results.timestamp)
            self.results_list.append(values_list)

            # EPANET simulator requires this to advance the simulation
            # self.wn.options.time.duration += self.wn.options.time.hydraulic_timestep
            master_time += 1
            try:
                # Update tank pressure
                for tank in self.tank_list:
                    tank_name = '\'' + tank + '\''
                    a_level = self.wn.get_node(tank).level
                    self.set_to_db(tank_name, a_level)

                # Update pump flow
                for pump in self.pump_list:
                    a_flowrate = Decimal(self.wn.get_link(pump).flow)
                    pump_name ='\'' + pump + a_flowrate + '\''
                    self.set_to_db(pump_name, a_flowrate)

                # Update valve flow
                for valve in self.valve_list:
                    a_flowrate = Decimal(self.wn.get_link(valve).flow)
                    valve_name ='\'' + valve + 'F' + '\''
                    self.set_to_db(valve_name, a_flowrate)

                # Update the SCADA junctions
                for junction in self.scada_junction_list:
                    junction_name = '\'' + junction + '\''
                    a_level = Decimal(self.wn.get_node(junction).head - self.wn.get_node(junction).elevation)
                    self.set_to_db(junction_name, a_level)

                self.set_to_db('CONTROL', 0)

                # For concealment attacks, we need more stages in the attack
                if self.attack_flag and (self.attack_type == "device_attack" or self.attack_type == "network_attack"):
                    if self.attack_start <= master_time < self.attack_end:
                        self.set_to_db('ATT_2', 1)
                    else:
                        self.set_to_db('ATT_2', 0)

            except Exception:
                print("Warning, skipping an iteration")
                continue

        self.write_results(self.results_list)


if __name__ == "__main__":
    simulation = PhysicalPlant()
    simulation.main()
