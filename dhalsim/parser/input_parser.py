import logging
import yaml

from antlr4 import *
from dhalsim.parser.antlr.controlsParser import controlsParser
from dhalsim.parser.antlr.controlsLexer import controlsLexer
from dhalsim.static.controls.ConcreteControl import *

logger = logging.getLogger(__name__)


class Error(Exception):
    """Base class for exceptions in this module."""


class NoInpFileGiven(Error):
    """Raised when tag you are looking for does not exist"""


class InputParser:
    """
    Class handling the parsing of .inp input files

    :param inp_path: The path of the inp file
    :type inp_path: str
    """

    def __init__(self, intermediate_yaml_path):
        """Constructor method
        """
        self.intermediate_yaml_path = intermediate_yaml_path
        with self.intermediate_yaml_path.open(mode='r') as intermediate_yaml:
            self.data = yaml.safe_load(intermediate_yaml)

        # Get the INP file path
        if 'inp_file' in self.data.keys():
            self.inp_file_path = self.data['inp_file']
        else:
            raise NoInpFileGiven()


    def write(self):
        # Generate PLC controls
        self.generate_controls()

        with self.intermediate_yaml_path.open(mode='w') as intermediate_yaml:
            yaml.safe_dump(self.data, intermediate_yaml)

    def generate_controls(self):
        input = FileStream(self.inp_file_path)
        tree = controlsParser(CommonTokenStream(controlsLexer(input))).controls()

        controls = []
        for i in range(0, tree.getChildCount()):
            child = tree.getChild(i)
            # Get all common control values from the control
            actuator = str(child.getChild(1))
            action = str(child.getChild(2))
            if child.getChildCount() == 7:
                # This is an AT NODE control
                dependant = str(child.getChild(4))
                value = float(str(child.getChild(6)))
                controls.append({
                    "type": str(child.getChild(5)).lower(),
                    "dependant": dependant,
                    "value": value,
                    "actuator": actuator,
                    "action": action
                })
            if child.getChildCount() == 5:
                # This is a TIME control
                value = float(str(child.getChild(4)))
                controls.append({
                    "type": "time",
                    "value": value,
                    "actuator": actuator,
                    "action": action
                })

        for plc in self.data['plcs']:
            plc['controls'] = []
            actuators = plc['actuators']
            for control in controls:
                if control['actuator'] in actuators:
                    plc['controls'].append(control)