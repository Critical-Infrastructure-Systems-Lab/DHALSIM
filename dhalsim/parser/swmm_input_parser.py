import sys

import pandas as pd
import wntr
from antlr4 import *

from ..epynet import epynetUtils
from ..epynet.network import WaterDistributionNetwork
from dhalsim.parser.antlr.controlsLexer import controlsLexer
from dhalsim.parser.antlr.controlsParser import controlsParser
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

        # todo

    def write(self):

        self.generate_times()

        self.read_initial_catchmend_values_from_inp()

        # Return the YAML object
        return self.data
