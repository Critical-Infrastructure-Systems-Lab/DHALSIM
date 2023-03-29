import sys

import pandas as pd
import wntr
from antlr4 import *

from ..epynet import epynetUtils
from ..epynet.network import WaterDistributionNetwork
from dhalsim.parser.antlr.controlsLexer import controlsLexer
from dhalsim.parser.antlr.controlsParser import controlsParser
from dhalsim.parser.antlr.subcatchmentsLexer import subcatchmentsLexer
from dhalsim.parser.antlr.subcatchmentsParser import subcatchmentsParser
from dhalsim.py3_logger import get_logger


class Error(Exception):
    """Base class for exceptions in this module."""


class NoInpFileGiven(Error):
    """Raised when tag you are looking for does not exist"""


class NotEnoughInitialValues(Error):
    """Raised when there are not enough initial values in a csv"""


def value_to_status(actuator_value):
    """
    Translates int corresponding to actuator status.

    :param actuator_value: The value from the status.value of the actuator
    :type actuator_value: int
    """
    if actuator_value == 0:
        return "closed"
    else:
        return "open"


class SwmmInputParser:

    def __init__(self, intermediate_yaml):
        """Constructor method"""
        self.data = intermediate_yaml

        self.logger = get_logger(self.data['log_level'])

        for plc in self.data['plcs']:
            if 'sensors' not in plc:
                plc['sensors'] = list()

            if 'actuators' not in plc:
                plc['actuators'] = list()

        # Get the INP file path
        if 'inp_file' in self.data.keys():
            self.inp_file_path = self.data['inp_file']
        else:
            raise NoInpFileGiven()
        # Read the inp file with WNTR
        self.simulator = self.data["simulator"]

    def generate_times(self):
        """
        Parses a pyswmm INP file to obtain the times required for the simulation.
        """
        # toDo

    def read_initial_catchmend_values_from_inp(self):
        """
        Parses the [LOADINGS] section of a pyswmm INP file to obtain initial pollutant values
        :return:
        """

        """
        input_file = FileStream(self.inp_file_path)
        tree = subcatchmentsParser(CommonTokenStream(controlsLexer(input_file))).loading()
        self.logger.debug('Controls tree')
        controls = []
        self.logger.debug(str(tree))
        #for i in range(0, tree.getChildCount()):
        #    child = tree.getChild(i)
        #    self.logger.debug(str(child))
        """


        state = 0
        tank_tuples = []
        with open(self.inp_file_path) as infile:
            for line in infile:
                if state == 0 and line.startswith('[LOADINGS]'):
                    state = 1
                    continue

                # Skip comments
                if state == 1 and line.startswith(';'):
                    continue
                if state == 1 and line.startswith('['):
                    break
                elif state == 1:
                    split_line = line.split()
                    if len(split_line) > 1:
                        tank_tuples.append((split_line[0], split_line[2]))

        self.data['initial_tank_values'] = dict(tank_tuples)
        self.logger.debug(str(self.data['initial_tank_values']))

    def generate_controls(self):
        """
        Generates list of controls with their types, values, actuators, and
        potentially dependant; then adds that to self.data to be written to the yaml.
        """
        input_file = FileStream(self.inp_file_path)
        tree = controlsParser(CommonTokenStream(subcatchmentsLexer(input_file))).controls()
        # self.logger.debug('Controls tree')
        controls = []
        for i in range(0, tree.getChildCount()):
            child = tree.getChild(i)
            # Get all common control values from the control
            actuator = str(child.getChild(2))
            action = str(child.getChild(4))

            if action == 'OPEN' or action == 'CLOSED':
                action_aux = action.lower()
            else:
                action_aux = float(action)

            if str(child.getChild(8)) == 'NODE':
                # This is an AT NODE control
                dependant = str(child.getChild(10))
                value = float(str(child.getChild(14)))

                controls.append({
                    "type": str(child.getChild(12)).lower(),
                    "dependant": dependant,
                    "value": value,
                    "actuator": actuator,
                    "action": action_aux
                })

                # self.logger.debug('control:\n' + str(controls[-1]))

            if str(child.getChild(8)) == 'TIME':
                # This is a TIME control
                value = float(str(child.getChild(10)))
                controls.append({
                    "type": "time",
                    "value": int(value),
                    "actuator": actuator,
                    "action": action_aux,
                })

        for plc in self.data['plcs']:
            plc['controls'] = []
            actuators = plc['actuators']
            for control in controls:
                if control['actuator'] in actuators:
                    plc['controls'].append(control)

    def generate_actuators_list(self):
        """
        Generates list of actuators with their initial states
        and adds to the data to be written to the yaml file.
        """

        pumps = []
        valves = []

        # Append valves to pumps
        pumps.extend(valves)
        self.data['actuators'] = pumps

    def write(self):

        # Generate PLC controls
        self.generate_controls()
        # Generate list of actuators + initial values
        self.generate_actuators_list()

        self.generate_times()

        self.read_initial_catchmend_values_from_inp()

        # Return the YAML object
        return self.data
