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
    # Network mocker patches
    mocker.patch(
        'dhalsim.python2.generic_plc.GenericPLC.receive',
        magic_mock_network.receive_multiple
    )
    mocker.patch(
        'dhalsim.python2.generic_plc.GenericPLC.get_sync',
        magic_mock_network.get_sync
    )
    mocker.patch(
        'dhalsim.python2.generic_plc.GenericPLC.set_sync',
        magic_mock_network.set_sync
    )


def test_python_version():
    assert sys.version_info.major is 2
    assert sys.version_info.minor is 7


