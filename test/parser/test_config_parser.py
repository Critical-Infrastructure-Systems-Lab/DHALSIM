import sys
from pathlib import Path
import pytest
import yaml

from dhalsim.parser.config_parser import ConfigParser, EmptyConfigError, MissingValueError, \
    InvalidValueError, DuplicateValueError


@pytest.fixture
def wadi_config_yaml_path():
    return Path("test/auxilary_testing_files/wadi_config.yaml")


def test_python_version():
    assert sys.version_info.major is 3


def test_file_not_found():
    with pytest.raises(FileNotFoundError):
        ConfigParser(Path("non_existing_path.yaml"))


def test_imp_path_good(tmpdir):
    c = tmpdir.join("config.yaml")
    inp_file = tmpdir.join("test.inp")
    inp_file.write("some: thing")
    c.write("inp_file: test.inp")
    parser = ConfigParser(Path(c))
    assert str(parser.inp_file) == str(tmpdir.join("test.inp"))


def test_imp_path_missing(tmpdir):
    c = tmpdir.join("config.yaml")
    c.write("something: else")
    parser = ConfigParser(Path(c))
    with pytest.raises(MissingValueError):
        parser.inp_file


def test_imp_path_not_found(tmpdir):
    c = tmpdir.join("config.yaml")
    c.write("inp_file: test.inp")
    parser = ConfigParser(Path(c))
    with pytest.raises(FileNotFoundError):
        parser.inp_file


def test_empty_config(tmpdir):
    c = tmpdir.join("config.yaml")
    c.write(" ")
    with pytest.raises(EmptyConfigError):
        ConfigParser(Path(c))


def test_cpa_path_good(tmpdir):
    c = tmpdir.join("config.yaml")
    inp_file = tmpdir.join("test.yaml")
    inp_file.write("plcs:\n - name: test")
    c.write("cpa_file: test.yaml")
    parser = ConfigParser(Path(c))
    assert str(parser.cpa_file) == str(tmpdir.join("test.yaml"))


def test_cpa_path_missing(tmpdir):
    c = tmpdir.join("config.yaml")
    c.write("something: else")
    parser = ConfigParser(Path(c))
    with pytest.raises(MissingValueError):
        parser.cpa_file


def test_cpa_path_not_found(tmpdir):
    c = tmpdir.join("config.yaml")
    c.write("cpa_file: test.yaml")
    parser = ConfigParser(Path(c))
    with pytest.raises(FileNotFoundError):
        parser.cpa_file


def test_cpa_data_path_good(tmpdir):
    c = tmpdir.join("config.yaml")
    cpa_file = tmpdir.join("test.yaml")
    cpa_file.write("plcs:\n - name: test")
    c.write("cpa_file: test.yaml")
    parser = ConfigParser(Path(c))
    assert parser.cpa_data == {'plcs': [{'name': 'test'}]}


def test_cpa_data_path_missing(tmpdir):
    c = tmpdir.join("config.yaml")
    c.write("something: else")
    parser = ConfigParser(Path(c))
    with pytest.raises(MissingValueError):
        parser.cpa_data


def test_cpa_missing_plcs(tmpdir):
    c = tmpdir.join("config.yaml")
    inp_file = tmpdir.join("test.yaml")
    inp_file.write("test: values")
    c.write("cpa_file: test.yaml")
    parser = ConfigParser(Path(c))
    with pytest.raises(MissingValueError):
        parser.cpa_data


def test_cpa_missing_plc_name(tmpdir):
    c = tmpdir.join("config.yaml")
    inp_file = tmpdir.join("test.yaml")
    inp_file.write("plcs:\n - not_name: test")
    c.write("cpa_file: test.yaml")
    parser = ConfigParser(Path(c))
    with pytest.raises(MissingValueError):
        parser.cpa_data


def test_cpa_data_path_not_found(tmpdir):
    c = tmpdir.join("config.yaml")
    c.write("cpa_file: test.yaml")
    parser = ConfigParser(Path(c))
    with pytest.raises(FileNotFoundError):
        parser.cpa_data


def test_config_parser_attacks(wadi_config_yaml_path):
    output = ConfigParser(wadi_config_yaml_path).generate_attacks({"plcs": [
        {"name": "PLC1", "actuators": ["P_RAW1", "V_PUB"], "sensors": ["T0"]},
        {"name": "PLC2", "actuators": ["V_ER2i"], "sensors": ["T2"]}
    ]})

    expected_output = {"plcs": [
        {"name": "PLC1", "actuators": ["P_RAW1", "V_PUB"], "sensors": ["T0"], "attacks": [
            {"name": "Close PRAW1 from iteration 5 to 10", "type": "Time",
             "actuators": ["P_RAW1"], "command": "closed", "start": 5, "end": 10},
            {"name": "Close PRAW1 when T2 < 0.16", "type": "Below",
             "actuators": ["P_RAW1"], "command": "closed", "sensor": "T2", "value": 0.16}
        ]},
        {"name": "PLC2", "actuators": ["V_ER2i"], "sensors": ["T2"]}
    ]}

    assert output == expected_output
    assert 'attacks' not in output['plcs'][1].keys()


def test_cpa_data_duplicate_name(tmpdir):
    c = tmpdir.join("config.yaml")
    cpa_file = tmpdir.join("test.yaml")
    cpa_file.write("plcs:\n - name: test \n - name: test")
    c.write("cpa_file: test.yaml")
    parser = ConfigParser(Path(c))
    with pytest.raises(DuplicateValueError):
        parser.cpa_data


def test_default_network_topology(tmpdir):
    c = tmpdir.join("config.yaml")
    c.write("something: else")
    parser = ConfigParser(Path(c))
    assert parser.network_topology_type == "simple"


def test_capital_network_topology_simple(tmpdir):
    c = tmpdir.join("config.yaml")
    c.write("network_topology_type: Simple")
    parser = ConfigParser(Path(c))
    assert parser.network_topology_type == "simple"


def test_capital_network_topology_complex(tmpdir):
    c = tmpdir.join("config.yaml")
    c.write("network_topology_type: Complex")
    parser = ConfigParser(Path(c))
    assert parser.network_topology_type == "complex"


def test_invalid_network_topology(tmpdir):
    c = tmpdir.join("config.yaml")
    c.write("network_topology_type: invalid")
    parser = ConfigParser(Path(c))
    with pytest.raises(InvalidValueError):
        parser.network_topology_type


def test_default_batch_mode(tmpdir):
    c = tmpdir.join("config.yaml")
    c.write("something: else")
    parser = ConfigParser(Path(c))
    assert parser.batch_mode is False


def test_true_batch_mode(tmpdir):
    c = tmpdir.join("config.yaml")
    c.write("batch_simulations: 12")
    parser = ConfigParser(Path(c))
    assert parser.batch_mode is True


def test_false_batch_mode(tmpdir):
    c = tmpdir.join("config.yaml")
    c.write("something: else")
    parser = ConfigParser(Path(c))
    assert parser.batch_mode is False


def test_invalid_batch_mode(tmpdir):
    c = tmpdir.join("config.yaml")
    c.write("batch_simulations: notanumber")
    parser = ConfigParser(Path(c))
    with pytest.raises(InvalidValueError):
        parser.batch_simulations


def test_initial_values_path_good(tmpdir):
    c = tmpdir.join("config.yaml")
    initial_values = tmpdir.join("test.yaml")
    initial_values.write("TANK\n5\n10")
    c.write("batch_mode: true\ninitial_tank_data: test.yaml")
    parser = ConfigParser(Path(c))
    assert str(parser.initial_tank_data) == str(tmpdir.join("test.yaml"))
