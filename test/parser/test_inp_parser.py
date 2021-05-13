import sys
import pytest
import yaml

from dhalsim.parser.input_parser import InputParser

@pytest.fixture
def inp_path(tmpdir):
    return tmpdir.join("input.inp")


@pytest.fixture
def initial_dict(inp_path):
    return {"inp_file": str(inp_path),
            "plcs": [{"name": "PLC1", "actuators": ["P_RAW1", "V_PUB"]}, {"name": "PLC2", "actuators": ["V_ER2i"]}]}


@pytest.fixture
def filled_dict(inp_path):
    return {"inp_file": str(inp_path),
            "plcs": [{"name": "PLC1",
                      "actuators": ["P_RAW1", "V_PUB"],
                      "controls": [{
                          "type": "below",
                          "dependant": "T0",
                          "value": 0.256,
                          "actuator": "V_PUB",
                          "action": "OPEN"
                      }, {
                          "type": "above",
                          "dependant": "T0",
                          "value": 0.448,
                          "actuator": "V_PUB",
                          "action": "CLOSED"
                      }]},
                     {"name": "PLC2",
                      "actuators": ["V_ER2i"],
                      "controls": [{
                          "type": "time",
                          "value": 0,
                          "actuator": "V_ER2i",
                          "action": "CLOSED"
                      }, {
                          "type": "above",
                          "dependant": "T2",
                          "value": 0.32,
                          "actuator": "V_ER2i",
                          "action": "CLOSED"
                      }]}]}


@pytest.fixture
def written_intermediate_yaml(tmpdir, initial_dict):
    intermediate = tmpdir.join("intermediate.yaml")
    with intermediate.open(mode='w') as intermediate_yaml:
        yaml.dump(initial_dict, intermediate_yaml)
    return tmpdir.join("intermediate.yaml")

def test_python_version():
    assert sys.version_info.major is 3


def test_no_controls(tmpdir, written_intermediate_yaml, filled_dict):
    inp = tmpdir.join("input.inp")
    inp.write("\n[CONTROLS]")

    InputParser(tmpdir.join("intermediate.yaml"))


def test_node_and_time_controls(tmpdir, written_intermediate_yaml, filled_dict):
    c = tmpdir.join("input.inp")
    c.write("\n"
            "[CONTROLS]\n"
            "LINK V_PUB  OPEN   IF NODE T0 BELOW 0.256\n"
            "LINK V_PUB  CLOSED IF NODE T0 ABOVE 0.448\n"
            "LINK V_ER2i CLOSED AT TIME 0\n"
            "LINK V_ER2i CLOSED IF NODE T2 ABOVE 0.32\n")

    InputParser(tmpdir.join("intermediate.yaml"))

    with tmpdir.join("intermediate.yaml").open(mode='r') as intermediate_yaml:
        dump = yaml.safe_load(intermediate_yaml)

    assert dump == filled_dict