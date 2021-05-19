import sys
from decimal import Decimal

import pytest
import pytest_mock
import yaml
from mock import MagicMock, call
from pathlib import Path

from dhalsim.python2.control import *
from dhalsim.python2.generic_plc import GenericPLC


@pytest.fixture
def magic_mock_network():
    mock = MagicMock()
    # network
    mock.get.return_value = u'42'
    mock.set.return_value = u'42'
    mock.receive.return_value = u'0.15'
    # database
    mock.get_sync.return_value = 0
    mock.set_sync.return_value = None
    return mock


@pytest.fixture
def magic_mock_init():
    mock = MagicMock()
    mock.do_super_construction.return_value = None
    mock.initialize_db.return_value = None
    return mock


@pytest.fixture
def magic_mock_preloop():
    mock = MagicMock()
    mock.set_parameters.return_value = None
    mock.startup.return_value = None
    mock.Lock.return_value = "testLock"
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
    }
    file = tmpdir.join("intermediate.yaml")
    with file.open(mode='w') as intermediate_yaml:
        yaml.dump(dict, intermediate_yaml)
    return file


def patch_methods(magic_mock_init, magic_mock_preloop, magic_mock_network, mocker):
    # Init mocker patches
    mocker.patch(
        'dhalsim.python2.generic_plc.GenericPLC.initialize_db',
        magic_mock_init.initialize_db
    )
    mocker.patch(
        'dhalsim.python2.generic_plc.GenericPLC.do_super_construction',
        magic_mock_init.do_super_construction
    )
    # Preloop mocker patches
    mocker.patch(
        'dhalsim.python2.basePLC.BasePLC.set_parameters',
        magic_mock_preloop.set_parameters
    )
    mocker.patch(
        'dhalsim.python2.basePLC.BasePLC.startup',
        magic_mock_preloop.startup
    )
    mocker.patch(
        'threading.Lock',
        magic_mock_preloop.Lock
    )
    # Network mocker patches
    mocker.patch(
        'dhalsim.python2.generic_plc.GenericPLC.get',
        magic_mock_network.get
    )
    mocker.patch(
        'dhalsim.python2.generic_plc.GenericPLC.set',
        magic_mock_network.set
    )
    mocker.patch(
        'dhalsim.python2.generic_plc.GenericPLC.receive',
        magic_mock_network.receive
    )
    mocker.patch(
        'dhalsim.python2.generic_plc.GenericPLC.get_sync',
        magic_mock_network.get_sync
    )
    mocker.patch(
        'dhalsim.python2.generic_plc.GenericPLC.set_sync',
        magic_mock_network.set_sync
    )


@pytest.fixture
def generic_plc1(mocker, yaml_file, magic_mock_init, magic_mock_preloop, magic_mock_network):
    patch_methods(magic_mock_init, magic_mock_preloop, magic_mock_network, mocker)
    return GenericPLC(Path(str(yaml_file)), 0)


@pytest.fixture
def generic_plc2(mocker, yaml_file, magic_mock_init, magic_mock_preloop, magic_mock_network):
    patch_methods(magic_mock_init, magic_mock_preloop, magic_mock_network, mocker)
    return GenericPLC(Path(str(yaml_file)), 1)


def test_python_version():
    assert sys.version_info.major is 2
    assert sys.version_info.minor is 7


def test_generic_plc1_init(generic_plc1, magic_mock_init, yaml_file):
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
            {"type": "Below", "dependant": "T2", "value": 0.16,
             "actuator": "P_RAW1", "action": "OPEN"}, ]}
    # Assert control generation
    assert len(generic_plc1.controls) == 1
    assert isinstance(generic_plc1.controls[0], BelowControl)
    assert generic_plc1.controls[0].value == 0.16
    assert generic_plc1.controls[0].dependant == "T2"
    assert generic_plc1.controls[0].action == "OPEN"
    assert generic_plc1.controls[0].actuator == "P_RAW1"
    # Assert proper function calls
    expected_calls = [call.initialize_db(),
                      call.do_super_construction(
                          {'server': {'tags': (('T0', 1, 'REAL'), ('T2', 1, 'REAL'), ('P_RAW1', 1, 'REAL')),
                                      'address': '192.168.1.1'}, 'name': 'enip', 'mode': 1},
                          {'path': '/home/test/dhalsim.sqlite', 'name': 'plant'})]
    assert magic_mock_init.mock_calls == expected_calls


def test_generic_plc2_init(generic_plc2, magic_mock_init, yaml_file):
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
            {"type": "Above", "dependant": "T2", "value": 0.32,
             "actuator": "V_ER2i", "action": "CLOSED"}, ]}
    # Assert control generation
    assert len(generic_plc2.controls) == 1
    assert isinstance(generic_plc2.controls[0], AboveControl)
    assert generic_plc2.controls[0].value == 0.32
    assert generic_plc2.controls[0].dependant == "T2"
    assert generic_plc2.controls[0].action == "CLOSED"
    assert generic_plc2.controls[0].actuator == "V_ER2i"
    # Assert proper function calls
    expected_calls = [call.initialize_db(),
                      call.do_super_construction({'server': {'tags': (('T2', 1, 'REAL'), ('V_ER2i', 1, 'REAL')),
                                                             'address': '192.168.1.2'}, 'name': 'enip', 'mode': 1},
                                                 {'path': '/home/test/dhalsim.sqlite', 'name': 'plant'})]
    assert magic_mock_init.mock_calls == expected_calls


def test_generic_plc1_preloop(generic_plc1, magic_mock_preloop, magic_mock_network):
    generic_plc1.pre_loop()
    # Verify pre loop function calls
    expected_preloop_calls = [call.Lock(),
                              call.set_parameters(generic_plc1,
                                                  [('T0', 1), ('P_RAW1', 1)],
                                                  [Decimal('42'), 42], True,
                                                  'testLock', '192.168.1.1'),
                              call.startup()]
    assert magic_mock_preloop.mock_calls == expected_preloop_calls
    # Verify network function calls
    expected_network_calls = [call.get(('T0', 1)), call.get(('P_RAW1', 1))]
    assert magic_mock_network.mock_calls == expected_network_calls


def test_generic_plc2_preloop(generic_plc2, magic_mock_preloop, magic_mock_network):
    generic_plc2.pre_loop()
    # Verify pre loop function calls
    expected_preloop_calls = [call.Lock(),
                              call.set_parameters(generic_plc2,
                                                  [('T2', 1), ('V_ER2i', 1)],
                                                  [Decimal('42'), 42], True,
                                                  'testLock', '192.168.1.2'),
                              call.startup()]
    assert magic_mock_preloop.mock_calls == expected_preloop_calls
    # Verify network function calls
    expected_network_calls = [call.get(('T2', 1)), call.get(('V_ER2i', 1))]
    assert magic_mock_network.mock_calls == expected_network_calls


def test_generic_plc1_mainloop(generic_plc1, magic_mock_network):
    generic_plc1.main_loop(test_break=True)
    # Verify network function calls (applying control rule)
    expected_network_calls = [call.get_sync(),
                              call.receive(('T2', 1), '192.168.1.2'),
                              call.set(('P_RAW1', 1), 1),
                              call.set_sync(1)]
    assert magic_mock_network.mock_calls == expected_network_calls


def test_generic_plc2_mainloop(generic_plc2, magic_mock_network):
    generic_plc2.main_loop(test_break=True)
    # Verify network function calls (applying control rule)
    expected_network_calls = [call.get_sync(),
                              call.get(('T2', 1)),
                              call.set(('V_ER2i', 1), 0),
                              call.set_sync(1)]
    assert magic_mock_network.mock_calls == expected_network_calls

