import sys
import pytest
import pytest_mock
import yaml
from mock import MagicMock, call
from pathlib import Path

from dhalsim.python2.control import *
from dhalsim.python2.generic_plc import GenericPLC


@pytest.fixture
def magic_mock():
    mock = MagicMock()
    mock.do_super_construction.return_value = 42
    mock.initialize_db.return_value = 42
    return mock


@pytest.fixture
def yaml_file(tmpdir):
    dict = {
        "db_path": "/home/test/dhalsim.sqlite",
        "plcs": [{"name": "PLC1",
                  "ip": "192.168.1.1",
                  "sensors": ["T0", ],
                  "actuators": ["P_RAW1", ],
                  "controls": [{"type": "Below",
                                "dependant": "T2",
                                "value": "0.16",
                                "actuator": "P_RAW1",
                                "action": "OPEN"}, ]
                  },
                 {"name": "PLC2",
                  "ip": "192.168.1.2",
                  "sensors": ["T2", ],
                  "actuators": ["V_ER2i", ],
                  "controls": [{"type": "Above",
                                "dependant": "T2",
                                "value": "0.32",
                                "actuator": "V_ER2i",
                                "action": "CLOSED"}, ]
                  }, ],
    }
    file = tmpdir.join("intermediate.yaml")
    with file.open(mode='w') as intermediate_yaml:
        yaml.dump(dict, intermediate_yaml)
    return file


@pytest.fixture
def generic_plc1(mocker, yaml_file, magic_mock):
    mocker.patch(
        'dhalsim.python2.generic_plc.GenericPLC.initialize_db',
        magic_mock
    )
    mocker.patch(
        'dhalsim.python2.generic_plc.GenericPLC.do_super_construction',
        magic_mock
    )
    return GenericPLC(Path(str(yaml_file)), 0)


@pytest.fixture
def generic_plc2(mocker, yaml_file, magic_mock):
    mocker.patch(
        'dhalsim.python2.generic_plc.GenericPLC.initialize_db',
        magic_mock
    )
    mocker.patch(
        'dhalsim.python2.generic_plc.GenericPLC.do_super_construction',
        magic_mock
    )
    return GenericPLC(Path(str(yaml_file)), 1)


def test_python_version():
    assert sys.version_info.major is 2
    assert sys.version_info.minor is 7


def test_generic_plc1_init(generic_plc1, magic_mock, yaml_file):
    # Check yaml index
    assert generic_plc1.yaml_index == 0
    # Load test yaml
    with yaml_file.open() as yaml_file_test:
        test_yaml = yaml.load(yaml_file_test, Loader=yaml.FullLoader)
    # Assert same as plc yaml
    assert generic_plc1.intermediate_yaml == test_yaml
    # Assert intermediate_plc correct
    assert generic_plc1.intermediate_plc == {"name": "PLC1", "ip": "192.168.1.1", "sensors": ["T0", ],
                                             "actuators": ["P_RAW1", ], "controls": [
            {"type": "Below", "dependant": "T2", "value": "0.16",
             "actuator": "P_RAW1", "action": "OPEN"}, ]}
    # Assert control generation
    assert len(generic_plc1.controls) == 1
    assert isinstance(generic_plc1.controls[0], BelowControl)
    assert generic_plc1.controls[0].value == "0.16"
    assert generic_plc1.controls[0].dependant == "T2"
    assert generic_plc1.controls[0].action == "OPEN"
    assert generic_plc1.controls[0].actuator == "P_RAW1"
    # Assert proper function calls
    expected_calls = [call.initialize_db(),
                      call.do_super_construction(
                          {'server': {'tags': (('T0', 1, 'REAL'), ('T2', 1, 'REAL'), ('P_RAW1', 1, 'REAL')),
                                      'address': '192.168.1.1'}, 'name': 'enip', 'mode': 1},
                          {'path': '/home/test/dhalsim.sqlite', 'name': 'plant'})]
    assert magic_mock.mock_calls == expected_calls


def test_generic_plc2_init(generic_plc2, magic_mock, yaml_file):
    # Check yaml index
    assert generic_plc2.yaml_index == 1
    # Load test yaml
    with yaml_file.open() as yaml_file_test:
        test_yaml = yaml.load(yaml_file_test, Loader=yaml.FullLoader)
    # Assert same as plc yaml
    assert generic_plc2.intermediate_yaml == test_yaml
    # Assert intermediate_plc correct
    assert generic_plc2.intermediate_plc == {"name": "PLC2", "ip": "192.168.1.2", "sensors": ["T2", ],
                                             "actuators": ["V_ER2i", ], "controls": [
            {"type": "Above", "dependant": "T2", "value": "0.32",
             "actuator": "V_ER2i", "action": "CLOSED"}, ]}
    # Assert control generation
    assert len(generic_plc2.controls) == 1
    assert isinstance(generic_plc2.controls[0], AboveControl)
    assert generic_plc2.controls[0].value == "0.32"
    assert generic_plc2.controls[0].dependant == "T2"
    assert generic_plc2.controls[0].action == "CLOSED"
    assert generic_plc2.controls[0].actuator == "V_ER2i"
    # Assert proper function calls
    expected_calls = [call.initialize_db(),
                      call.do_super_construction({'server': {'tags': (('T2', 1, 'REAL'), ('V_ER2i', 1, 'REAL')),
                                                             'address': '192.168.1.2'}, 'name': 'enip', 'mode': 1},
                                                 {'path': '/home/test/dhalsim.sqlite', 'name': 'plant'})]
    assert magic_mock.mock_calls == expected_calls
