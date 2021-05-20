import sys
from pathlib import Path
import pytest
import yaml

from dhalsim.parser.config_parser import ConfigParser, EmptyConfigError, MissingValueError, DuplicateValueError


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
    assert str(parser.inp_path) == str(tmpdir.join("test.inp"))


def test_imp_path_missing(tmpdir):
    c = tmpdir.join("config.yaml")
    c.write("something: else")
    parser = ConfigParser(Path(c))
    with pytest.raises(MissingValueError):
        parser.inp_path


def test_imp_path_not_found(tmpdir):
    c = tmpdir.join("config.yaml")
    c.write("inp_file: test.inp")
    parser = ConfigParser(Path(c))
    with pytest.raises(FileNotFoundError):
        parser.inp_path


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
    assert str(parser.cpa_path) == str(tmpdir.join("test.yaml"))


def test_cpa_path_missing(tmpdir):
    c = tmpdir.join("config.yaml")
    c.write("something: else")
    parser = ConfigParser(Path(c))
    with pytest.raises(MissingValueError):
        parser.cpa_path


def test_cpa_path_not_found(tmpdir):
    c = tmpdir.join("config.yaml")
    c.write("cpa_file: test.yaml")
    parser = ConfigParser(Path(c))
    with pytest.raises(FileNotFoundError):
        parser.cpa_path


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
    ConfigParser(wadi_config_yaml_path).generate_intermediate_yaml()

    with Path("/tmp/dhalsim/intermediate.yaml").open(mode='r') as written_file:
        written_data = yaml.safe_load(written_file)

    with Path("test/auxilary_testing_files/intermediate-wadi-attack.yaml").open(mode='r') as expectation:
        expected_data = yaml.safe_load(expectation)

    assert written_data['plcs'][0]['attacks'] == expected_data['plcs'][0]['attacks']
    assert 'attacks' not in written_data['plcs'][1].keys()

def test_cpa_data_duplicate_name(tmpdir):
    c = tmpdir.join("config.yaml")
    cpa_file = tmpdir.join("test.yaml")
    cpa_file.write("plcs:\n - name: test \n - name: test")
    c.write("cpa_file: test.yaml")
    parser = ConfigParser(Path(c))
    with pytest.raises(DuplicateValueError):
        parser.cpa_data
