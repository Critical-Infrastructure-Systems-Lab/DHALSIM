import logging

from antlr4 import *
from dhalsim.parser.antlr.controlsParser import controlsParser
from dhalsim.parser.antlr.controlsLexer import controlsLexer
from dhalsim.static.Controls.ConcreteControl import *

logger = logging.getLogger(__name__)


class InputParser:
    """
    Class handling the parsing of .inp input files

    :param inp_path: The path of the inp file
    :type inp_path: str
    """

    def __init__(self, inp_path):
        """Constructor method
        """
        self.inp_path = inp_path

        logger.debug("inp file: %s", inp_path)

    def generate_controls(self):
        input = FileStream(self.inp_path)
        lexer = controlsLexer(input)
        stream = CommonTokenStream(lexer)
        parser = controlsParser(stream)
        tree = parser.controls()

        controls = []
        for i in range(0, tree.getChildCount()):
            child = tree.getChild(i)
            # Get all common control values from the control
            actuator = str(child.getChild(1))
            action = str(child.getChild(2))
            if child.getChildCount() == 7:
                # This is an AT NODE control
                # Get other common control values
                dependant = str(child.getChild(4))
                value = str(child.getChild(6))
                if str(child.getChild(5)) == "BELOW":
                    # This is a BelowControl
                    controls.append(BelowControl(actuator, action, dependant, value))
                if str(child.getChild(5)) == "ABOVE":
                    # This is a BelowControl
                    controls.append(AboveControl(actuator, action, dependant, value))
            if child.getChildCount() == 5:
                value = str(child.getChild(4))
                controls.append(TimeControl(actuator, action, "TIME", value))

        return controls
