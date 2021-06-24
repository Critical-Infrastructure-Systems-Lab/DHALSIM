import sys
from pathlib import Path

import pytest
import yaml
from mock import MagicMock, call

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
def yaml_file(tmpdir):
    dict = {
        "log_level": "info",
        "db_path": "/home/test/dhalsim.sqlite",
        "plcs": [{"name": "PLC1",
                  "local_ip": "192.168.1.1",
                  "public_ip": "192.168.1.1",
                  "sensors": ["T0", ],
                  "actuators": ["P_RAW1", ],
                  "controls": [{"type": "Below",
                                "dependant": "T2",
                                "value": 0.16,
                                "actuator": "P_RAW1",
                                "action": "OPEN"},
                               {"type": "Below",
                                "dependant": "T2",
                                "value": 0.16,
                                "actuator": "P_RAW1",
                                "action": "CLOSED"}, ]
                  },
                 {"name": "PLC2",
                  "local_ip": "192.168.1.2",
                  "public_ip": "192.168.1.2",
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


def patch_methods(magic_mock_init, magic_mock_network, mocker):
    # Init mocker patches
    mocker.patch(
        'dhalsim.python2.generic_plc.GenericPLC.initialize_db',
        magic_mock_init.initialize_db
    )
    mocker.patch(
        'dhalsim.python2.generic_plc.GenericPLC.do_super_construction',
        magic_mock_init.do_super_construction
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
def generic_plc1(mocker, yaml_file, magic_mock_init, magic_mock_network):
    patch_methods(magic_mock_init, magic_mock_network, mocker)
    return GenericPLC(Path(str(yaml_file)), 0)


def test_python_version():
    assert sys.version_info.major is 2
    assert sys.version_info.minor is 7


def test_generic_plc1_cache(generic_plc1, magic_mock_network):
    generic_plc1.main_loop(test_break=True)
    # Verify network function calls (applying control rule)
    expected_network_calls = [call.get_sync(),
                              call.receive(('T2', 1), '192.168.1.2'),  # Only called once
                              call.set(('P_RAW1', 1), 1),
                              call.set(('P_RAW1', 1), 0),
                              call.set_sync(1)]
    assert magic_mock_network.mock_calls == expected_network_calls
