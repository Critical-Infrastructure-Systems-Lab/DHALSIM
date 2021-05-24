import sys
import pytest
import yaml
from pathlib import Path

from dhalsim.parser.input_parser import InputParser


@pytest.fixture
def inp_path(tmpdir):
    return Path("test/auxilary_testing_files/wadi_map_pda_original.inp")


@pytest.fixture
def initial_dict(inp_path):
    return {"inp_file": str(inp_path),
            "batch_mode": False,
            "plcs": [{"name": "PLC1", "actuators": ["P_RAW1", "V_PUB"], "sensors": ["T0"]},
                     {"name": "PLC2", "actuators": ["V_ER2i"], "sensors": ["T2"]}]}


@pytest.fixture
def filled_yaml_path():
    return Path("test/auxilary_testing_files/intermediate-wadi-pda-original.yaml")


@pytest.fixture
def written_intermediate_yaml(tmpdir, initial_dict):
    intermediate = tmpdir.join("intermediate.yaml")
    with intermediate.open(mode='w') as intermediate_yaml:
        yaml.dump(initial_dict, intermediate_yaml)
    return tmpdir.join("intermediate.yaml")


def test_python_version():
    assert sys.version_info.major is 3


def test_node_and_time_controls(tmpdir, written_intermediate_yaml, filled_yaml_path):
    with written_intermediate_yaml.open(mode='r') as intermediate_yaml:
        original_data = yaml.safe_load(intermediate_yaml)

    filled_data = InputParser(original_data).write()

    with filled_yaml_path.open(mode='r') as expectation:
        expected = yaml.safe_load(expectation)

    assert filled_data == expected
