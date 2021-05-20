import sys
from decimal import Decimal

import pytest
import pytest_mock
import yaml
from mock import MagicMock, call
from pathlib import Path

from dhalsim.python2.generic_scada import GenericScada


@pytest.fixture
def magic_mock_network():
    mock = MagicMock()
    # network
    mock.receive_multiple.return_value = u'0.15'
    # database
    mock.get_sync.return_value = 0
    mock.set_sync.return_value = None
    return mock


@pytest.fixture
def magic_mock_init():
    mock = MagicMock()
    mock.do_super_construction.return_value = None
    mock.initialize_db.return_value = None
    mock.touch.return_value = None
    return mock


@pytest.fixture
def magic_mock_preloop():
    mock = MagicMock()
    mock.signal.return_value = None
    return mock


@pytest.fixture
def yaml_file(tmpdir):
    dict = {
        "db_path": "/home/test/dhalsim.sqlite",
        "output_path": "/home/test/dhalsim/output",
        "scada": {"name": "scada",
                  "ip": "192.168.2.1"},
        "plcs": [{"name": "PLC1",
                  "ip": "192.168.1.1",
                  "sensors": ["T0", ],
                  "actuators": ["P_RAW1", ],
                  "controls": [{"type": "Below",
                                "dependant": "T2",
                                "value": 0.16,
                                "actuator": "P_RAW1",
                                "action": "OPEN"}, ]
                  },
                 {"name": "PLC2",
                  "ip": "192.168.1.2",
                  "sensors": ["T2", ],
                  "actuators": ["V_ER2i", ],
                  "controls": [{"type": "Above",
                                "dependant": "T2",
                                "value": 0.32,
                                "actuator": "V_ER2i",
                                "action": "CLOSED"}, ]
                  }, ],
        "tanks": [{"name": "T0"}, {"name": "T2"}],
        "pumps": [{"name": "P_RAW1"}],
        "valves": [{"name": "V_ER2i"}],
    }
    file = tmpdir.join("intermediate.yaml")
    with file.open(mode='w') as intermediate_yaml:
        yaml.dump(dict, intermediate_yaml)
    return file


def patch_methods(magic_mock_init, magic_mock_preloop, magic_mock_network, mocker):
    # Init mocker patches
    mocker.patch(
        'dhalsim.python2.generic_scada.GenericScada.initialize_db',
        magic_mock_init.initialize_db
    )
    mocker.patch(
        'dhalsim.python2.generic_scada.GenericScada.do_super_construction',
        magic_mock_init.do_super_construction
    )
    mocker.patch(
        'pathlib.Path.touch',
        magic_mock_init.touch
    )
    # Preloop mocker patches
    mocker.patch(
        'signal.signal',
        magic_mock_preloop.signal
    )
    # Network mocker patches
    mocker.patch(
        'dhalsim.python2.generic_scada.GenericScada.receive',
        magic_mock_network.receive_multiple
    )
    mocker.patch(
        'dhalsim.python2.generic_scada.GenericScada.get_sync',
        magic_mock_network.get_sync
    )
    mocker.patch(
        'dhalsim.python2.generic_scada.GenericScada.set_sync',
        magic_mock_network.set_sync
    )


@pytest.fixture
def generic_scada(mocker, yaml_file, magic_mock_init, magic_mock_preloop, magic_mock_network):
    patch_methods(magic_mock_init, magic_mock_preloop, magic_mock_network, mocker)
    return GenericScada(Path(str(yaml_file)))


def test_python_version():
    assert sys.version_info.major is 2
    assert sys.version_info.minor is 7


def test_generic_scada_init(generic_scada, magic_mock_init, yaml_file):
    # Load test yaml
    with yaml_file.open() as yaml_file_test:
        test_yaml = yaml.load(yaml_file_test, Loader=yaml.FullLoader)
    # Assert same as plc yaml
    assert generic_scada.intermediate_yaml == test_yaml
    # Assert intermediate_plc correct
    assert str(generic_scada.output_path) == "/home/test/dhalsim/output/scada_values.csv"
    # Assert plc data generation
    assert generic_scada.plc_data == [('192.168.1.1', [('T0', 1), ('P_RAW1', 1)]),
                                      ('192.168.1.2', [('T2', 1), ('V_ER2i', 1)])]
    # Assert plc saved values generation
    assert generic_scada.saved_values == [['T0', 'P_RAW1', 'T2', 'V_ER2i']]
    # Assert proper function calls
    expected_calls = [call.initialize_db(), call.touch(exist_ok=True),
                      call.do_super_construction({'server': {
                          'tags': (('T0', 1, 'REAL'), ('T2', 1, 'REAL'), ('P_RAW1', 1, 'REAL'), ('V_ER2i', 1, 'REAL')),
                          'address': '192.168.2.1'}, 'name': 'enip', 'mode': 1},
                          {'path': '/home/test/dhalsim.sqlite', 'name': 'plant'})]
    assert magic_mock_init.mock_calls == expected_calls
