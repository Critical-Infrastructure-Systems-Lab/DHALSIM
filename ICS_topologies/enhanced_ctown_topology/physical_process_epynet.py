import sqlite3
import csv
import sys
import os
import pandas as pd
import yaml
from decimal import Decimal
from datetime import datetime

sys.path.insert(1, sys.path[0] + '/epynet/scripts')

print(sys.path)

import network
import epynet_utils

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

        # connection to the database
        self.db_path = config_options['db_path']
        self.conn = sqlite3.connect(self.db_path)
        self.c = self.conn.cursor()

        self.output_path = config_options['output_ground_truth_path']
        self.simulation_days = int(config_options['duration_days'])

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
        total_demands = pd.read_csv(patterns_path, index_col=0)
        demand_starting_points = pd.read_csv(starting_demand, index_col=0)

        week_start = demand_starting_points.iloc[self.week_index][0]
        week_demands = total_demands.loc[week_start:week_start + limit, :]

        print("Week_demands: " + str(week_demands))
        print("wn.patterns" + str(list(self.wn.patterns.keys())))

        for pattern in list(self.wn.patterns.keys()):
            print("Values: " + str(week_demands[pattern].values.tolist()))
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
                #self.configure_demand_patterns(demand_patterns_path, starting_demand_path)

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

    def get_actuator_status(self, table, actuator):
        act_name = '\'' + actuator + '\''
        rows_1 = self.c.execute('SELECT value FROM ' + table + ' WHERE name = ' + act_name).fetchall()
        self.conn.commit()
        return int(rows_1[0][0])

    def update_actuators(self):
        for actuator in self.actuator_list:
            self.actuator_list[actuator] = self.get_actuator_status('ctown', actuator)

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
            rows = self.c.execute("SELECT value FROM ctown WHERE name = 'ATT_1'").fetchall()
            self.conn.commit()
            attack1 = int(rows[0][0])
            rows = self.c.execute("SELECT value FROM ctown WHERE name = 'ATT_2'").fetchall()
            self.conn.commit()
            attack2 = int(rows[0][0])
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

    def write_to_db(self, db_name, attribute, value):
        query = "UPDATE " + db_name + " SET value = " + str(value) + " WHERE name = " + attribute
        self.c.execute(query)  # UPDATE TANKS IN THE DATABASE
        self.conn.commit()

    def main(self):

        # toDO: These parameters need to be imported form the yaml file
        simluation_step = 300
        simulation_duration = self.simulation_days * 24 * 3600
        #simulation_duration = 3600

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

        # FOR DEBUG
        #status = [1.0, 0.0]
        #actuators_status_dict = {uid: status for uid in self.wn.pumps.uid.append(self.wn.valves.uid)}

        while internal_epynet_step > 0:

            self.update_actuators()
            #print("Simulating with actuators: " + str(self.actuator_list))
            internal_epynet_step, network_state = self.wn.simulate_step(simulation_time, self.actuator_list)

            if internal_epynet_step == simluation_step:
                master_time += 1

            print("Internal epynet step: " + str(internal_epynet_step))
            print("ITERATION %d ------------- " % master_time)

            #print("Network State")
            #print(network_state)

            step_results = self.register_results(network_state)

            #print("Step Results")
            #print(step_results)

            self.results_list.append(step_results)

            simulation_time = simulation_time + internal_epynet_step
            #continue


            try:
                # Update tank pressure
                for tank in self.tank_list:
                    tank_name = '\'' + tank + '\''
                    a_level = Decimal(network_state[tank]['pressure'])
                    self.write_to_db('ctown', tank_name, a_level)

                # Update pump flow
                for pump in self.pump_list:
                    a_flowrate = Decimal(network_state[pump]['flow'])
                    pump_name = '\'' + pump + 'F' + '\''
                    self.write_to_db('ctown', pump_name, a_flowrate)

                # Update valve flow
                for valve in self.valve_list:
                    a_flowrate = Decimal(network_state[valve]['flow'])
                    valve_name = '\'' + valve + 'F' + '\''
                    self.write_to_db('ctown', valve_name, a_flowrate)

                # Update the SCADA junctions
                #print(self.scada_junction_list)
                for junction in self.scada_junction_list:
                    junction_name = '\'' + junction + '\''
                    a_level = Decimal(self.wn.junctions[junction].pressure.iloc[-1])
                    self.write_to_db('ctown', junction_name, a_level)

                query = "UPDATE ctown SET value = 0 WHERE name = 'CONTROL'"
                self.c.execute(query)  # UPDATE CONTROL value for the PLCs to apply control
                self.conn.commit()

                # For concealment attacks, we need more stages in the attack
                if self.attack_flag and (self.attack_type == "device_attack" or self.attack_type == "network_attack"):
                    if self.attack_start <= master_time < self.attack_end:
                        query = "UPDATE ctown SET value = " + str(1) + " WHERE name = 'ATT_2'"
                        self.c.execute(query)  # UPDATE ATT_2 value for the plc1 to launch attack
                        self.conn.commit()
                    else:
                        query = "UPDATE ctown SET value = " + str(0) + " WHERE name = 'ATT_2'"
                        self.c.execute(query)  # UPDATE ATT_2 value for the plc1 to stop attack
                        self.conn.commit()

            except Exception as ex:
                print("Warning, skipping an iteration")
                print(ex)
                continue

        self.write_results(self.results_list)

if __name__ == "__main__":
    simulation = PhysicalPlant()
    simulation.main()