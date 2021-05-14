from dhalsim.physical_process import PhysicalPlant
from mock import patch
from wntr.network import WaterNetworkModel
from wntr.sim import WNTRSimulator
from pytest import raises
from pathlib import Path


# TODO:
# test other functions in physical_process.py

def get_physical_plant():
    """
    Gets an instance of PhysicalPlant, using intermediate.yaml at auxilary_testing_files.
    """
    return PhysicalPlant(Path('../auxilary_testing_files/intermediate.yaml'))
