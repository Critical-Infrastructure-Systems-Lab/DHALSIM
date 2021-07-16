from dhalsim.physical_process import PhysicalPlant
from pathlib import Path
import pytest
import filecmp
import yaml

@pytest.fixture
def no_controls_path(tmpdir):
    return Path("test/auxilary_testing_files/wadi_map_pda_original_no_controls.inp")

@pytest.fixture
def controls_path(tmpdir):
    return Path("test/auxilary_testing_files/wadi_map_pda_original.inp")

@pytest.fixture
def filled_yaml_path():
    return Path("test/auxilary_testing_files/intermediate-wadi-pda-original.yaml")


def get_physical_plant():
    """
    Gets an instance of PhysicalPlant, using intermediate.yaml at auxilary_testing_files.
    """
    return PhysicalPlant(Path('../auxilary_testing_files/intermediate.yaml'))

#def test_remove_controls_from_inp_for_epynet(tmpdir, no_controls_path, controls_path, filled_yaml_path):
#    with filled_yaml_path.open(mode='r') as intermediate_yaml:
#        options = yaml.safe_load(intermediate_yaml)
#        plant = PhysicalPlant(intermediate_yaml)

#    original_inp_filename = options['inp_file'].rsplit('.', 1)[0]
#    processed_inp_filename = original_inp_filename + '_processed.inp'

    #no_controls_original = no_controls_path.open(mode='r')
    #no_control_process = processed_inp_filename.open(mode='r')

    #filecmp.cmp(no_controls_path, processed_inp_filename, shallow=True)
