import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml

from dhalsim.parser.config_parser import ConfigParser


@pytest.fixture
def wadi_config_yaml_path():
    return Path("test/auxilary_testing_files/wadi_config.yaml")


@pytest.fixture
def filled_yaml_path():
    return Path("test/auxilary_testing_files/intermediate.yaml")


@pytest.fixture
def directory_mock(tmpdir):
    mock = MagicMock()
    mock.mkdtemp.return_value = str(tmpdir)
    mock.chmod.return_value = None
    return mock


def test_python_version():
    assert sys.version_info.major is 3


def test_config_parser_attacks(wadi_config_yaml_path):
    output = ConfigParser(wadi_config_yaml_path).generate_device_attacks({"plcs": [
        {"name": "PLC1", "actuators": ["P_RAW1", "V_PUB"], "sensors": ["T0"]},
        {"name": "PLC2", "actuators": ["V_ER2i"], "sensors": ["T2"]}
    ]})

    expected_output = {"plcs": [
        {"name": "PLC1", "actuators": ["P_RAW1", "V_PUB"], "sensors": ["T0"], "attacks": [
            {"name": "Close PRAW1 from iteration 5 to 10", "trigger": {"type": "Time", "start": 5, "end": 10},
             "actuator": "P_RAW1", "command": "closed"},
            {"name": "Close PRAW1 when T2 < 0.16", "trigger": {"type": "Below", "sensor": "T2", "value": 0.16},
             "actuator": "P_RAW1", "command": "closed"}
        ]},
        {"name": "PLC2", "actuators": ["V_ER2i"], "sensors": ["T2"]}
    ]}

    assert output == expected_output
    assert 'attacks' not in output['plcs'][1].keys()


def test_generate_intermediate_yaml(mocker, tmpdir, wadi_config_yaml_path, filled_yaml_path, directory_mock):
    mocker.patch(
        'tempfile.mkdtemp',
        directory_mock.mkdtemp
    )
    mocker.patch(
        'os.chmod',
        directory_mock.chmod
    )

    with filled_yaml_path.open(mode='r') as expectation:
        expected = yaml.safe_load(expectation)

    # Because paths are dynamic, overwrite it in expected output
    expected['db_path'] = directory_mock.mkdtemp() + '/dhalsim.sqlite'
    local_path = str(Path(__file__).absolute().parent.parent)
    expected['inp_file'] = local_path + '/auxilary_testing_files/wadi_map_pda_original.inp'
    expected['output_path'] = local_path + '/auxilary_testing_files/output'

    yaml_path = ConfigParser(wadi_config_yaml_path).generate_intermediate_yaml()

    print(yaml_path)

    with yaml_path.open(mode='r') as reality:
        actual = yaml.safe_load(reality)

    assert actual == expected
    directory_mock.mkdtemp.assert_called_with(prefix='dhalsim_')
    directory_mock.chmod.assert_called_with(directory_mock.mkdtemp(), 0o777)
