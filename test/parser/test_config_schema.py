import sys
from pathlib import Path

import pytest
from schema import SchemaError

from dhalsim.parser.config_parser import ConfigParser


def test_python_version():
    assert sys.version_info.major is 3


@pytest.fixture
def test_dict():
    return {
        "inp_file": Path(),
        "network_topology_type": "simple",
        "output_path": Path(),
        "iterations": 10,
        "mininet_cli": False,
        "log_level": "info",
        "simulator": "pdd",
        "batch_simulations": 3,
        "initial_tank_data": Path(),
        "demand_patterns": Path(),
        "network_loss_data": Path(),
        "network_delay_data": Path(),
        "run_attack": True,
        "plcs": [
            {"name": "PLC1", "sensors": ["T0"], "actuators": ["P_RAW1", "V_PUB"]},
            {"name": "PLC2", "sensors": ["T2"], "actuators": ["V_ER2i"]},
        ],

        "attacks": {
            "device_attacks": [
                {
                    "name": "Close_PRAW1_from_iteration_5_to_10",
                    "trigger": {
                        "type": "Time",
                        "start": 5,
                        "end": 10
                    },
                    "actuator": "P_RAW1",
                    "command": "closed",
                }
            ]
        },
    }


@pytest.fixture
def attack_dict_1():
    return {
        'name': 'test1',
        'tags': [{'tag': 'T2', 'value': 0.2}],
        'target': 'PLC2',
        'trigger': {'end': 7, 'start': 2, 'type': 'Time'},
        'type': 'mitm'
    }


@pytest.fixture
def attack_dict_2():
    return {'name': 'test2',
            'target': 'PLC1',
            'trigger': {'end': 17, 'start': 12, 'type': 'Time'},
            'type': 'naive_mitm',
            'value': -2}


def test_valid_dict(test_dict):
    ConfigParser.validate_schema(test_dict)
    assert True


@pytest.mark.parametrize("key, default_value", [
    ('network_topology_type', 'simple'),
    ('mininet_cli', False),
    ('log_level', 'info'),
    ('simulator', 'pdd')
])
def test_default_config(key, default_value, test_dict):
    del test_dict[key]
    result = ConfigParser.validate_schema(test_dict)
    assert result[key] == default_value


@pytest.mark.parametrize("key", [
    'iterations',
    'batch_simulations',
    'initial_tank_data',
    'demand_patterns',
    'network_loss_data',
    'network_delay_data',
    'attacks',
])
def test_optional_config(key, test_dict):
    del test_dict[key]
    result = ConfigParser.validate_schema(test_dict)
    assert result.get(key) is None


@pytest.mark.parametrize("required_key", ['inp_file', 'plcs'])
def test_required_config(required_key, test_dict):
    del test_dict[required_key]
    with pytest.raises(SchemaError):
        ConfigParser.validate_schema(test_dict)


@pytest.mark.parametrize("key, invalid_value", [
    ('network_topology_type', 2),
    ('network_topology_type', 'invalid'),
    ('network_topology_type', ''),
    ('iterations', '5'),
    ('iterations', 10.5),
    ('iterations', -10),
    ('iterations', 0),
    ('mininet_cli', "False"),
    ('mininet_cli', "True"),
    ('mininet_cli', ""),
    ('mininet_cli', 1),
    ('mininet_cli', 0),
    ('log_level', 1),
    ('log_level', "invalid"),
    ('log_level', ""),
    ('simulator', 1),
    ('simulator', "invalid"),
    ('simulator', ""),
    ('run_attack', "False"),
    ('run_attack', "True"),
    ('run_attack', ""),
    ('run_attack', 1),
    ('run_attack', 0),
    ('batch_simulations', '5'),
    ('batch_simulations', 10.5),
    ('batch_simulations', -10),
    ('batch_simulations', 0),
])
def test_invalid_config(key, invalid_value, test_dict):
    test_dict[key] = invalid_value
    with pytest.raises(SchemaError):
        ConfigParser.validate_schema(test_dict)


@pytest.mark.parametrize("key, input_value, expected_value", [
    ('network_topology_type', 'simple', 'simple'),
    ('network_topology_type', 'SIMPLE', 'simple'),
    ('network_topology_type', 'complex', 'complex'),
    ('network_topology_type', 'COMPLEX', 'complex'),
    ('iterations', 100, 100),
    ('mininet_cli', True, True),
    ('mininet_cli', False, False),
    ('log_level', 'debug', 'debug'),
    ('log_level', 'DEBUG', 'debug'),
    ('log_level', 'info', 'info'),
    ('log_level', 'INFO', 'info'),
    ('log_level', 'warning', 'warning'),
    ('log_level', 'WARNING', 'warning'),
    ('log_level', 'error', 'error'),
    ('log_level', 'ERROR', 'error'),
    ('log_level', 'critical', 'critical'),
    ('log_level', 'CRITICAL', 'critical'),
    ('simulator', 'pdd', 'pdd'),
    ('simulator', 'PDD', 'pdd'),
    ('simulator', 'dd', 'dd'),
    ('simulator', 'DD', 'dd'),
    ('run_attack', True, True),
    ('run_attack', False, False),
    ('batch_simulations', 100, 100),
])
def test_valid_config(key, input_value, expected_value, test_dict):
    test_dict[key] = input_value
    output = ConfigParser.validate_schema(test_dict)
    assert output[key] == expected_value


@pytest.mark.parametrize("key", [
    'actuators',
    'sensors',
])
def test_optional_plcs(key, test_dict):
    del test_dict['plcs'][0][key]
    result = ConfigParser.validate_schema(test_dict)
    assert result.get(key) is None


@pytest.mark.parametrize("required_key", ['name'])
def test_required_plcs(required_key, test_dict):
    del test_dict['plcs'][0][required_key]
    with pytest.raises(SchemaError):
        ConfigParser.validate_schema(test_dict)


@pytest.mark.parametrize("key, invalid_value", [
    ('name', ''),
    ('name', 'PLC 1'),
    ('name', 1),
    ('name', 0),
    ('name', 'plc#1'),
    ('name', '&'),
    ('name', ' plc1'),
    ('sensors', ["T 0"]),
    ('sensors', [" T0"]),
    ('sensors', ["T#0"]),
    ('sensors', [5]),
    ('sensors', [4.2]),
    ('sensors', ['&']),
    ('sensors', ["木头"]),
    ('actuators', ["V 0"]),
    ('actuators', [" V0"]),
    ('actuators', ["V#0"]),
    ('actuators', [5]),
    ('actuators', [4.2]),
    ('actuators', ['&']),
    ('actuators', ["木头"]),
])
def test_invalid_plc(key, invalid_value, test_dict):
    test_dict['plcs'][0][key] = invalid_value
    with pytest.raises(SchemaError):
        ConfigParser.validate_schema(test_dict)


@pytest.mark.parametrize("key, input_value, expected_value", [
    ('name', 'plc1', 'plc1'),
    ('name', 'PLc1', 'PLc1'),
    ('name', 'PLC100', 'PLC100'),
    ('name', 'thing', 'thing'),
    ('name', '123', '123'),
    ('name', 'plc_1', 'plc_1'),
    ('sensors', ["T0", "T1"], ["T0", "T1"]),
    ('sensors', ["Tank"], ["Tank"]),
    ('sensors', [], []),
    ('sensors', ["tank_42"], ["tank_42"]),
    ('actuators', ["V0", "V1"], ["V0", "V1"]),
    ('actuators', ["Valve"], ["Valve"]),
    ('actuators', [], []),
    ('actuators', ["valve_42"], ["valve_42"]),
])
def test_valid_plc(key, input_value, expected_value, test_dict):
    test_dict['plcs'][0][key] = input_value
    output = ConfigParser.validate_schema(test_dict)
    assert output['plcs'][0][key] == expected_value


def test_attack_dicts(attack_dict_1, attack_dict_2):
    ConfigParser.network_attacks.validate(attack_dict_1)
    ConfigParser.network_attacks.validate(attack_dict_2)


@pytest.mark.parametrize("key, input_value", [
    ('type', 9),
    ('type', 'hi')
])
def test_invalid_attacks_mitm(key, input_value, attack_dict_1):
    attack_dict_1[key] = input_value
    with pytest.raises(SchemaError):
        ConfigParser.validate_schema(attack_dict_1)


@pytest.mark.parametrize("key, input_value, expected", [
    ('name', 'hello', 'hello'),
])
def test_valid_attacks_mitm(key, input_value, expected, attack_dict_1):
    attack_dict_1[key] = input_value
    output = ConfigParser.network_attacks.validate(attack_dict_1)
    assert output[key] == expected


@pytest.mark.parametrize("key, input_value", [
    ('type', 9),
    ('type', 'hi')
])
def test_invalid_attacks_naive(key, input_value, attack_dict_2):
    attack_dict_2[key] = input_value
    with pytest.raises(SchemaError):
        ConfigParser.validate_schema(attack_dict_2)


@pytest.mark.parametrize("key, input_value, expected", [
    ('name', 'hello', 'hello'),
])
def test_valid_attacks_naive(key, input_value, expected, attack_dict_2):
    attack_dict_2[key] = input_value
    output = ConfigParser.network_attacks.validate(attack_dict_2)
    assert output[key] == expected


@pytest.mark.parametrize("required_key", [
    'name',
    'type',
    'trigger',
    'target'
])
def test_required_attack_fields_mitm(required_key, attack_dict_1):
    del attack_dict_1[required_key]
    with pytest.raises(SchemaError):
        ConfigParser.validate_schema(attack_dict_1)


@pytest.mark.parametrize("required_key", [
    'name',
    'type',
    'trigger',
    'target'
])
def test_required_attack_fields_naive(required_key, attack_dict_2):
    del attack_dict_2[required_key]
    with pytest.raises(SchemaError):
        ConfigParser.validate_schema(attack_dict_2)
