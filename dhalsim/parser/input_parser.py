import logging
import yaml
import wntr

from antlr4 import *
from dhalsim.parser.antlr.controlsParser import controlsParser
from dhalsim.parser.antlr.controlsLexer import controlsLexer
from dhalsim.static.controls.ConcreteControl import *

logger = logging.getLogger(__name__)


class Error(Exception):
    """Base class for exceptions in this module."""


class NoInpFileGiven(Error):
    """Raised when tag you are looking for does not exist"""


def value_to_status(actuator_value):
    """Translates int corresponding to actuator status

    :param actuator_value: The value from the status.value of the actuator
    :type actuator_value: int
    """
    if actuator_value == 0:
        return "closed"
    else:
        return "open"


class InputParser:
    """Class handling the parsing of .inp input files

    :param intermediate_yaml_path: The path of the inp file
    :type intermediate_yaml_path: str
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
        # Read the inp file with WNTR
        self.wn = wntr.network.WaterNetworkModel(self.inp_file_path)


    def write(self):
        """Writes all needed inp file sections into the intermediate_yaml
        """
        # Generate PLC controls
        self.generate_controls()
        # Generate list of pumps + initial values
        self.generate_pumps_list()
        # Generate list of valves + initial values
        self.generate_valves_list()
        # Generate list of tanks + initial values
        self.generate_tanks_list()
        # Generate list of times
        self.generate_times()
        # Write to the yaml
        with self.intermediate_yaml_path.open(mode='w') as intermediate_yaml:
            yaml.safe_dump(self.data, intermediate_yaml)

    def generate_controls(self):
        """Generates list of controls with their types, values, actuators, and
        potentially dependant; then adds that to self.data to be written to the yaml
        """
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
                    "action": action.lower()
                })
            if child.getChildCount() == 5:
                # This is a TIME control
                value = float(str(child.getChild(4)))
                controls.append({
                    "type": "time",
                    "value": int(value),
                    "actuator": actuator,
                    "action": action.lower()
                })

        for plc in self.data['plcs']:
            plc['controls'] = []
            actuators = plc['actuators']
            for control in controls:
                if control['actuator'] in actuators:
                    plc['controls'].append(control)

    def generate_pumps_list(self):
        """Generates list of pumps with their initial states and
        adds it to the data to be written to the yaml file
        """
        pumps = []
        for pump in self.wn.pumps():
            pumps.append({
                "name": pump[0],
                "initial_state": value_to_status(pump[1].status.value)
            })
        self.data['pumps'] = pumps

    def generate_valves_list(self):
        """Generates list of valves with their initial states and
        adds it to the data to be written to the yaml file
        """
        valves = []
        for valve in self.wn.valves():
            valves.append({
                "name": valve[0],
                "initial_state": value_to_status(valve[1].status.value)
            })
        self.data['valves'] = valves

    def generate_tanks_list(self):
        """Generates list of tanks with their initial values and
        adds it to the data to be written to the yaml file-
        """
        tanks = []
        for tank in self.wn.tanks():
            tanks.append({
                "name": tank[0],
                "initial_value": self.wn.get_node(tank[0]).init_level
            })
            self.data['tanks'] = tanks

    def generate_times(self):
        """Generates duration and hydraulic timestep and adds to the
        data to be written to the yaml file
        """

        # TODO Decide on the timestep (minutes or seconds?)
        times = [
            {"duration": self.wn.options.time.duration},
            {"hydraulic_timestep": self.wn.options.time.hydraulic_timestep}
        ]
        self.data['time'] = times