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
                  "actuators": ["V_PUB", ],
                  "controls": [{"type": "Below",
                                "dependant": "T0",
                                "value": "0.256",
                                "actuator": "V_PUB",
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
                                             "actuators": ["V_PUB", ], "controls": [
            {"type": "Below", "dependant": "T0", "value": "0.256",
             "actuator": "V_PUB", "action": "OPEN"}, ]}
    # Assert control generation
    assert len(generic_plc1.controls) == 1
    assert isinstance(generic_plc1.controls[0], BelowControl)
    assert generic_plc1.controls[0].value == "0.256"
    assert generic_plc1.controls[0].dependant == "T0"
    assert generic_plc1.controls[0].action == "OPEN"
    assert generic_plc1.controls[0].actuator == "V_PUB"
    # Assert proper function calls
    expected_calls = [call.initialize_db(),
                      call.do_super_construction({'server': {'tags': (('T0', 1, 'REAL'), ('V_PUB', 1, 'REAL')),
                                                             'address': '192.168.1.1'}, 'name': 'enip', 'mode': 1},
                                                 {'path': '/home/test/dhalsim.sqlite', 'name': 'plant'})]
    assert magic_mock.mock_calls == expected_calls
