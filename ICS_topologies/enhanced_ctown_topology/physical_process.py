import wntr
import wntr.network.controls as controls
import sqlite3
import csv
import sys
import pandas as pd
import yaml
from utils import flag_attack_plc1, flag_attack_communication_plc1_plc2, \
    flag_attack_communication_plc1_plc2_replay_empty


class PhysicalPlant:

    def __init__(self):

        # toDo: This is were we change the parameters received by this script to create a generic physical process.
        #config_file_path = "wadi_config.yaml"
        config_file_path = sys.argv[1]
        config_options = self.load_config(config_file_path)

        # Week index to initialize the simulation
        if "week_index" in config_options:
            self.week_index = int(config_options['week_index'])
        else:
            self.week_index = 0

        # connection to the database
        self.db_path = config_options['db_path']
        self.conn = sqlite3.connect(self.db_path)
        self.c = self.conn.cursor()

        self.output_path = config_options['output_ground_truth_path']
        self.simulation_days = int(config_options['duration_days'])

        # Create the network
        inp_file = config_options['inp_file']
        self.wn = wntr.network.WaterNetworkModel(inp_file)

        self.node_list = list(self.wn.node_name_list)
        self.link_list = list(self.wn.link_name_list)

        self.tank_list = self.get_node_list_by_type(self.node_list, 'Tank')
        self.junction_list = self.get_node_list_by_type(self.node_list, 'Junction')
        self.pump_list = self.get_link_list_by_type(self.link_list, 'Pump')
        self.valve_list = self.get_link_list_by_type(self.link_list, 'Valve')

        list_header = ["Timestamps"]
        aux = self.create_node_header(self.tank_list)
        list_header.extend(aux)

        aux = self.create_node_header(self.junction_list)
        list_header.extend(aux)

        aux = self.create_link_header(self.pump_list)
        list_header.extend(aux)
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
            a_control = controls.Control(control['condition'], an_action, name=control['name'])
            self.wn.add_control(control['name'], a_control)

        simulator_string = config_options['simulator']

        if simulator_string == 'pdd':
            print('Running simulation using PDD')
            self.sim = wntr.sim.WNTRSimulator(self.wn, mode='PDD')
            # sim = wntr.sim.EpanetSimulator(wn)
        elif simulator_string == 'dd':
            print('Running simulation using DD')
            self.sim = wntr.sim.WNTRSimulator(self.wn)
        else:
            print('Invalid simulation mode, exiting...')
            sys.exit(1)

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

    def initialize_simulation(self, config_options):

        if self.simulation_days == 7:
            limit = 167
        else:
            limit = 239

        if 'initial_custom_flag' in config_options:
            custom_initial_conditions_flag =  bool(config_options['initial_custom_flag'])
            if custom_initial_conditions_flag:
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

        rows = self.c.execute("SELECT value FROM ctown WHERE name = 'ATT_1'").fetchall()
        self.conn.commit()
        attack1 = int(rows[0][0])
        rows = self.c.execute("SELECT value FROM ctown WHERE name = 'ATT_2'").fetchall()
        self.conn.commit()
        attack2 = int(rows[0][0])

        values_list.extend([attack1, attack2])
        return values_list

    def update_controls(self):
        for control in self.control_list:
            self.update_control(control)

    def update_control(self, control):
        act_name = '\'' + control['name'] + '\''
        rows_1 = self.c.execute('SELECT value FROM ctown WHERE name = ' + act_name).fetchall()
        self.conn.commit()
        new_status = int(rows_1[0][0])

        control['value'] = new_status

        # act1 = controls.ControlAction(pump1, 'status', int(pump1_status))
        new_action = controls.ControlAction(control['actuator'], control['parameter'], control['value'])

        # pump1_control = controls.Control(condition, act1, name='pump1control')
        new_control = controls.Control(control['condition'], new_action, name=control['name'])

        self.wn.remove_control(control['name'])
        self.wn.add_control(control['name'], new_control)

    def write_results(self, results):
        with open('output/' + self.output_path, 'w') as f:
            writer = csv.writer(f)
            writer.writerows(results)

    def main(self):
        # We want to simulate only 1 hydraulic timestep each time MiniCPS processes the simulation data
        self.wn.options.time.duration = self.wn.options.time.hydraulic_timestep
        master_time = 0

        #self.simulation_days = 1

        iteration_limit = (self.simulation_days * 24 * 3600) / self.wn.options.time.hydraulic_timestep

        print("Simulation will run for " + str(self.simulation_days) + " days. Hydraulic timestep is " + str(
            self.wn.options.time.hydraulic_timestep) +
              " for a total of " + str(iteration_limit) + " iterations ")

        while master_time <= iteration_limit:
            #tic
            self.update_controls()
            #toc
            print("ITERATION %d ------------- " % master_time)
            results = self.sim.run_sim(convergence_error=True)
            #toc
            values_list = self.register_results(results)

            self.results_list.append(values_list)
            master_time += 1

            for tank in self.tank_list:
                tank_name = '\'' + tank + '\''
                a_level = self.wn.get_node(tank).level
                query = "UPDATE ctown SET value = " + str(a_level) + " WHERE name = " + tank_name
                self.c.execute(query)  # UPDATE TANKS IN THE DATABASE
                self.conn.commit()

            if flag_attack_plc1 == 1 or flag_attack_communication_plc1_plc2 == 1:
                if 648 <= master_time < 1153:
                    query = "UPDATE ctown SET value = " + str(1) + " WHERE name = 'ATT_2'"
                    self.c.execute(query)  # UPDATE ATT_2 value for the plc1 to launch attack
                    self.conn.commit()
                else:
                    query = "UPDATE ctown SET value = " + str(0) + " WHERE name = 'ATT_2'"
                    self.c.execute(query)  # UPDATE ATT_2 value for the plc1 to stop attack
                    self.conn.commit()
            #toc
            if flag_attack_communication_plc1_plc2_replay_empty == 1:
                if 648 <= master_time < 1153:
                    query = "UPDATE ctown SET value = " + str(1) + " WHERE name = 'ATT_2'"
                    self.c.execute(query)  # UPDATE ATT_2 value for the plc1 to launch attack
                    self.conn.commit()
                else:
                    query = "UPDATE ctown SET value = " + str(0) + " WHERE name = 'ATT_2'"
                    self.c.execute(query)  # UPDATE ATT_2 value for the plc1 to stop attack
                    self.conn.commit()

        self.write_results(self.results_list)

if __name__=="__main__":
    simulation = PhysicalPlant()
    simulation.main()