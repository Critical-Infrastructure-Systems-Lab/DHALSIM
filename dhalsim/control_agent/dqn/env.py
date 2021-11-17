import pandas as pd
import threading
import numpy as np
import random
import time
import sqlite3
import sys
import yaml
import logging

from dhalsim import py3_logger
from mushroom_rl.core.environment import Environment, MDPInfo
from mushroom_rl.utils.spaces import Discrete, Box

from dhalsim.control_agent.dqn.obj_function import step_supply_demand_ratio, supply_demand_ratio, fake_obj_funtion
from dhalsim.epynet.network import WaterDistributionNetwork

lock = threading.Lock()


class Error(Exception):
    """Base class for exceptions in this module."""


class DatabaseError(Error):
    """Raised when not being able to connect to the database"""


class WaterNetworkEnvironment(Environment):
    """

    """
    # Amount of times a db query will retry on a exception
    DB_TRIES = 10

    # Amount of time a db query will wait before retrying
    DB_SLEEP_TIME = random.uniform(0.01, 0.1)

    def __init__(self, agent_config_file, intermediate_yaml_path):
        """
        Initialize the environment of the control problem.

        :param agent_config_file: agent configuration file
        :type agent_config_file: Path

        :param intermediate_yaml_path: current simulation intermediate yaml file
        :type intermediate_yaml_path: Path
        """
        with agent_config_file.open(mode='r') as fin:
            self.config_data = yaml.safe_load(fin)

        self.intermediate_yaml = None
        self.hyd_step = None
        self.set_intermediate_yaml(intermediate_yaml_path)
        self.demand_pattern = None
        self.demand_moving_average = None
        self.logger = py3_logger.get_logger('info')

        self.state_vars = self.config_data['env']['state_vars']
        self.action_vars = self.config_data['env']['action_vars']
        # self.bounds = self.config_data['env']['bounds']

        # Used to update the pump status every a certain amount of time (e.g. every 4 hours)
        self.update_every = self.config_data['env']['update_every']

        # Current state
        self._state = None

        self.done = False
        self.old_status_dict = None
        self.state_dict_from_db = {}

        self.total_supplies = []
        self.total_demands = []
        self.total_updates = 0
        self.dsr = 0

        self.conn = sqlite3.connect(self.intermediate_yaml['db_control_path'])
        self.cur = self.conn.cursor()

        # Control database prepared statement
        self._table_name = ['state_space', 'action_space']
        self._value = 'value'
        self._what = tuple()
        self._set_query = None
        self._get_query = None

        self._init_what()

        if not self._what:
            raise ValueError('Primary key not found.')
        else:
            self._init_get_query()
            self._init_set_query()

        # Two possible values for each pump: 2 ^ n_pumps
        action_space = Discrete(2 ** len(self.action_vars))

        # Bounds for observation space
        lows = np.array([self.state_vars[key]['bounds']['min'] for key in self.state_vars.keys()])
        highs = np.array([self.state_vars[key]['bounds']['max'] for key in self.state_vars.keys()])

        # Observation space
        observation_space = Box(low=lows, high=highs, shape=(len(self.state_vars),))

        # TODO: what is horizon?
        mdp_info = MDPInfo(observation_space, action_space, gamma=0.99, horizon=1000000)
        super().__init__(mdp_info)
        # print("ENVIRONMENT CREATED")

    def set_intermediate_yaml(self, intermediate_yaml_path):
        """
        Set the intermediate yaml file of the current simulation.

        :param intermediate_yaml_path: path of the current intermediate yaml
        :type intermediate_yaml_path: Path
        """
        with intermediate_yaml_path.open(mode='r') as fin:
            self.intermediate_yaml = yaml.safe_load(fin)

        # Set the hydraulic timestep, useful to get the elapsed time
        self.hyd_step = self.intermediate_yaml['time']['hydraulic_timestep'][1]

    def _init_what(self):
        """
        Save a ordered tuple of pk field names in self._what
        """
        query = "PRAGMA table_info(%s)" % self._table_name[0]

        try:
            self.cur.execute(query)
            table_info = self.cur.fetchall()

            # last tuple element
            primary_keys = []
            for field in table_info:
                if field[-1] > 0:
                    primary_keys.append(field)

            if not primary_keys:
                print('ERROR: Please provide at least 1 primary key. Has sqlite DB been initialized?. Aborting!')
                sys.exit(1)
            else:
                # sort by pk order
                primary_keys.sort(key=lambda x: x[5])

                what_list = []
                for pk in primary_keys:
                    what_list.append(pk[1])

                self._what = tuple(what_list)

        except sqlite3.Error as e:
            print('ERROR: Error initializing the sqlite DB. Exiting. Error: ' + str(e))
            sys.exit(1)

    def _init_set_query(self):
        """
        Prepared statement to update action_space table.
        """
        set_query = 'UPDATE %s SET %s = ? WHERE %s = ?' % (
            self._table_name[1],
            self._value,
            self._what[0])

        # for composite pk
        for pk in self._what[1:]:
            set_query += ' AND %s = ?' % (
                pk)

        self._set_query = set_query

    def _init_get_query(self):
        """
        Prepared statement to retrieve the observation space from state_space table.
        """
        get_query = 'SELECT %s FROM %s WHERE %s = ?' % (
            self._value,
            self._table_name[0],
            self._what[0])

        # for composite pk
        for pk in self._what[1:]:
            get_query += ' AND %s = ?' % (
                pk)

        self._get_query = get_query

    def db_query(self, query, parameters=None):
        """
        Execute a query on the database.
        On a :code:`sqlite3.OperationalError` it will retry with a max of :code:`DB_TRIES` tries.
        Before it reties, it will sleep for :code:`DB_SLEEP_TIME` seconds.
        This is necessary because of the limited concurrency in SQLite.

        :param query: The SQL query to execute in the db
        :type query: str

        :param parameters: The parameters to put in the query
        :type parameters: tuple

        :raise DatabaseError: When a :code:`sqlite3.OperationalError` is still raised after
           :code:`DB_TRIES` tries.
        """
        for i in range(self.DB_TRIES):
            try:
                if parameters:
                    self.cur.execute(query, parameters)
                else:
                    self.cur.execute(query)
                return
            except sqlite3.OperationalError as exc:
                print(
                    "ERROR: Failed to connect to db with exception {exc}. Trying {i} more times.".format(
                        exc=exc, i=self.DB_TRIES - i - 1))
                time.sleep(self.DB_SLEEP_TIME)
        print("ERROR: Failed to connect to db. Tried {i} times.".format(i=self.DB_TRIES))
        raise DatabaseError("Failed to get master clock from database")

    def get_sync(self):
        """
        Get the sync flag of the scada before the beginning of the control step.
        On a :code:`sqlite3.OperationalError` it will retry with a max of :code:`DB_TRIES` tries.
        Before it reties, it will sleep for :code:`DB_SLEEP_TIME` seconds.

        :return: False if physical process wants the plc to do a iteration, True if not.

        :raise DatabaseError: When a :code:`sqlite3.OperationalError` is still raised after
           :code:`DB_TRIES` tries.
        """
        # Get sync from control_db
        self.db_query("SELECT flag FROM sync WHERE name IS 'scada'")
        flag = bool(self.cur.fetchone()[0])
        return flag

    def set_sync(self):
        """
        Set the agent's sync flag in the sync table and removes the scada's one.
        When this is 1, the scada process knows that the agent finished the control iteration.
        On a :code:`sqlite3.OperationalError` it will retry with a max of :code:`DB_TRIES` tries.
        Before it reties, it will sleep for :code:`DB_SLEEP_TIME` seconds.

        :raise DatabaseError: When a :code:`sqlite3.OperationalError` is still raised after
           :code:`DB_TRIES` tries.
        """
        self.db_query("UPDATE sync SET flag=1 WHERE name IS 'agent'")
        self.db_query("UPDATE sync SET flag=0 WHERE name IS 'scada'")
        self.conn.commit()

    def check_scada_ready(self):
        """
        Check if the scada has completed its operations.

        :return: 1 if scada has finished, 0 otherwise.
        """
        flag = self.get_sync()
        return flag

    def write_db(self, node_id, value):
        """
        Set new state space values inside the action_space table.

        :param node_id: name of the considered couple (node, property)
        :type node_id: basestring

        :param value: value of the property
        :type value: float
        """
        query_args = (value, node_id)

        self.db_query(query=self._set_query, parameters=query_args)
        self.conn.commit()

    def read_db(self, node_id):
        """
        Read the values of the observation space and retrieve them.

        :param node_id: name of the considered couple (node, property)
        :type node_id: basestring

        :return: value of the actuator status
        """
        query_args = (node_id,)

        self.db_query(query=self._get_query, parameters=query_args)
        record = self.cur.fetchone()
        return record[0]

    def check_done_flag(self):
        """
        Check if the simulation is ended and the SCADA has sent the done flag.

        :return: the done flag (1 if it has been set, 0 otherwise)
        """
        flag = self.read_db(node_id='done')
        if flag:
            return True
        else:
            return False

    def build_current_state(self):
        """
        Build current state list, which can be used as input of the nn saved_models
        The structure of the state space can be retrieved in the agent_config file.

        :return: list of the current state space
        """
        state = []
        # self.state_dict = {}

        # Save the database data in a dictionary
        for var in self.config_data['env']['db_state_vars']:
            self.state_dict_from_db[var] = self.read_db(node_id=var)

        elapsed_time = self.state_dict_from_db['sim_step'] * self.hyd_step
        seconds_per_day = 3600 * 24
        days_per_week = 7
        current_hour = (elapsed_time % (seconds_per_day * days_per_week)) // 3600

        #self.logger.info("state_dict: " + str(self.state_dict_from_db))

        # Build the state as requested by the neural network
        for var in self.state_vars.keys():
            if var in self.state_dict_from_db.keys():
                state.append(self.state_dict_from_db[var])
            if var == 'time':
                state.append(elapsed_time % seconds_per_day)
            if var == 'day':
                state.append(((elapsed_time // seconds_per_day) % days_per_week) + 1)
            if var == 'demand_SMA':
                # print(self.demand_moving_average.iloc[current_hour, 0])
                state.append(self.demand_moving_average.iloc[current_hour, 0])

        return [np.float32(i) for i in state]

    def send_new_action(self, actuators):
        """
        Send to database the new action retrieved from the control step.

        :param actuators: dictionary of actuators with their new status value
        :type actuators: dict
        """
        for var in actuators.keys():
            self.write_db(node_id=var, value=actuators[var])

        self.set_sync()

    def reset(self, state=None):
        """
        Reset the environment at the start of a new episode.

        :return: the starting state of the episode
        """
        self.done = False
        self.total_demands = []
        self.total_supplies = []
        self.total_updates = 0
        self.old_status_dict = None

        # Set demand pattern taken in the intermediate_yaml and computes the moving average
        self.demand_pattern = pd.read_csv(self.intermediate_yaml['demand_patterns_data'])
        #print(self.demand_pattern)
        self.demand_moving_average = self.demand_pattern.rolling(window=self.state_vars['demand_SMA']['window'],
                                                                 min_periods=1).mean()
        #print(self.demand_moving_average)
        self._state = self.build_current_state()
        return self._state

    def step(self, action):
        """
        Step function called by the Core object to take a step into the control problem.

        :param action: action retrieved by the epsilon greedy policy that has to be applied

        :return: new current state after the step, last computed reward, absorbing state flag and information about the
                 simulation (if coded)
        """
        n_updates = 0

        # Action transformation from binary format to boolean one (0 or 1)
        new_status_dict = {pump_id: 0 for pump_id in self.action_vars}
        bin_action = '{0:0{width}b}'.format(action[0], width=len(self.action_vars))

        for i, key in enumerate(new_status_dict.keys()):
            new_status_dict[key] = int(bin_action[i])

        # Register the number of updates done wrt the last step
        if self.old_status_dict is not None:
            for key in new_status_dict.keys():
                if new_status_dict[key] != self.old_status_dict[key]:
                    n_updates += 1
        self.old_status_dict = new_status_dict
        self.total_updates += n_updates

        # Update action_table
        self.send_new_action(new_status_dict)

        while not self.check_scada_ready():
            #print("wait")
            time.sleep(0.01)

        # Get new state space
        self._state = self.build_current_state()

        reward = self.compute_reward(n_updates)
        info = None

        # check if done
        self.done = self.check_done_flag()
        if self.done:
            #print(self.done)
            self.dsr = self.evaluate()

        return self._state, reward, self.done, info

    def render(self):
        pass

    def check_overflow(self):
        """
        Check if the we have an overflow problem in the tanks. We have an overflow if after one hour we the tank is
        still at the maximum level.
        :return: penalty value
        """
        penalty = 1.1
        risk_percentage = 0.9

        for key in self.state_dict_from_db:
            if key[0] == 'T':
                if self.state_dict_from_db[key] >= self.state_vars[key]['bounds']['max']:
                    out_bound = self.state_dict_from_db[key] - (self.state_vars[key]['bounds']['max'] * risk_percentage)
                    # Normalization of the out_bound pressure
                    multiplier = out_bound / ((1 - risk_percentage) * self.state_vars[key]['bounds']['max'])
                    return penalty * multiplier
        return 0

    def compute_reward(self, n_updates):
        """
        Compute the reward function: the DSR value with penalties due to updates of actuators' status.

        :param n_updates: number of updates of actuators' status
        :type n_updates: int
        """
        current_supplies = []
        current_demands = []

        for var in self.config_data['obj_func']['supplies']:
            current_supplies.append(self.read_db(node_id=var))

        for var in self.config_data['obj_func']['basedemands']:
            current_demands.append(self.read_db(node_id=var))

        self.total_supplies.append(current_supplies)
        self.total_demands.append(current_demands)

        #print("basedemands: " + str(current_demands))
        #print("supplies: " + str(current_supplies))

        updates_penalty = n_updates / 2
        overflow_penalty = self.check_overflow()
        dsr_ratio = step_supply_demand_ratio(supplies=current_supplies, base_demands=current_demands)

        reward = -updates_penalty + dsr_ratio - overflow_penalty
        # print(">>> current reward: ", reward)
        return reward

    def evaluate(self):
        """
        Evaluate the model at the end of the episode.
        """
        return supply_demand_ratio(self.total_supplies, self.total_demands)
