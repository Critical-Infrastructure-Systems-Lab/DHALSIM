import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml

from dhalsim.parser.config_parser import ConfigParser, TooManyNodes


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
    assert sys.version_info.major == 3


def test_config_parser_attacks(wadi_config_yaml_path):
    output = ConfigParser(wadi_config_yaml_path).generate_device_attacks({"plcs": [
        {"name": "PLC1", "actuators": ["P_RAW1", "V_PUB"], "sensors": ["T0"]},
        {"name": "PLC2", "actuators": ["V_ER2i"], "sensors": ["T2"]}
    ]})

    expected_output = {"plcs": [
        {"name": "PLC1", "actuators": ["P_RAW1", "V_PUB"], "sensors": ["T0"], "attacks": [
            {"name": "Close_PRAW1_from_iteration_5_to_10",
             "trigger": {"type": "time", "start": 5, "end": 10},
             "actuator": "P_RAW1", "command": "closed"},
            {"name": "Close_PRAW1_when_T2_<_0.16",
             "trigger": {"type": "below", "sensor": "T2", "value": 0.16},
             "actuator": "P_RAW1", "command": "closed"}
        ]},
        {"name": "PLC2", "actuators": ["V_ER2i"], "sensors": ["T2"]}
    ]}

    assert output == expected_output
    assert 'attacks' not in output['plcs'][1].keys()


def test_generate_intermediate_yaml(mocker, tmpdir, wadi_config_yaml_path, filled_yaml_path,
                                    directory_mock):
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

    actual.pop('config_path')
    actual.pop('start_time')

    assert actual == expected
    directory_mock.mkdtemp.assert_called_with(prefix='dhalsim_')
    directory_mock.chmod.assert_called_with(directory_mock.mkdtemp(), 0o775)


@pytest.mark.parametrize('plcs, network_attacks',
                         [
                             (10, 10),
                             (0, 250),
                             (250, 0),
                             (10, 240),
                         ])
def test_not_to_many_nodes_good_weather(plcs, network_attacks):
    plcs = [i for i in range(plcs)]
    network_attacks = [i for i in range(network_attacks)]
    ConfigParser.not_to_many_nodes({'plcs': plcs, 'attacks': {'network_attacks': network_attacks}})


@pytest.mark.parametrize('network_attacks',
                         [
                             10,
                             250,
                             0,
                         ])
def test_not_to_many_nodes_no_plcs_good_weather(network_attacks):
    network_attacks = [i for i in range(network_attacks)]
    ConfigParser.not_to_many_nodes({'attacks': {'network_attacks': network_attacks}})


@pytest.mark.parametrize('plcs',
                         [
                             10,
                             250,
                             0,
                         ])
def test_not_to_many_nodes_no_network_attacks_good_weather(plcs):
    plcs = [i for i in range(plcs)]
    ConfigParser.not_to_many_nodes({'plcs': plcs})


@pytest.mark.parametrize('plcs, network_attacks',
                         [
                             (10, 241),
                             (0, 251),
                             (251, 0),
                             (11, 240),
                         ])
def test_not_to_many_nodes_bad_weather(plcs, network_attacks):
    plcs = [i for i in range(plcs)]
    network_attacks = [i for i in range(network_attacks)]
    with pytest.raises(TooManyNodes):
        ConfigParser.not_to_many_nodes({'plcs': plcs, 'attacks': {'network_attacks': network_attacks}})


@pytest.mark.parametrize('network_attacks',
                         [
                             251,
                             1000000,
                         ])
def test_not_to_many_nodes_no_plcs_bad_weather(network_attacks):
    network_attacks = [i for i in range(network_attacks)]
    with pytest.raises(TooManyNodes):
        ConfigParser.not_to_many_nodes({'attacks': {'network_attacks': network_attacks}})


@pytest.mark.parametrize('plcs',
                         [
                             251,
                             100000,
                         ])
def test_not_to_many_nodes_no_network_attacks_bad_weather(plcs):
    plcs = [i for i in range(plcs)]
    with pytest.raises(TooManyNodes):
        ConfigParser.not_to_many_nodes({'plcs': plcs})
