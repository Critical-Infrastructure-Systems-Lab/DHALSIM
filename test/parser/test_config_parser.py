import sys
from pathlib import Path

import pytest

from dhalsim.parser.config_parser import ConfigParser, EmptyConfigError, MissingValueError


def test_python_version():
    assert sys.version_info.major is 3


@pytest.fixture
def inp_data_fixture():
    return """[TITLE]\n[CONTROLS]\nLINK V_PUB OPEN IF NODE T1 BELOW 0.256\nLINK V_ER2i CLOSED AT TIME 0\n"""


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
    inp_file.write("some: thing")
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
    cpa_file.write("some: thing")
    c.write("cpa_file: test.yaml")
    parser = ConfigParser(Path(c))
    assert parser.cpa_data == {"some": "thing"}


def test_cpa_data_path_missing(tmpdir):
    c = tmpdir.join("config.yaml")
    c.write("something: else")
    parser = ConfigParser(Path(c))
    with pytest.raises(MissingValueError):
        parser.cpa_data


def test_cpa_data_path_not_found(tmpdir):
    c = tmpdir.join("config.yaml")
    c.write("cpa_file: test.yaml")
    parser = ConfigParser(Path(c))
    with pytest.raises(FileNotFoundError):
        parser.cpa_data


# def test_generate_intermediate_yaml_no_plcs(tmpdir, inp_data_fixture):
#     c = tmpdir.join("config.yaml")
#     cpa_file = tmpdir.join("test.yaml")
#     cpa_file.write("some: thing")
#     c.write("cpa_file: test.yaml\ninp_file: input.inp")
#
#     inp_file = tmpdir.join("input.inp")
#     inp_file.write(inp_data_fixture)
#
#     parser = ConfigParser(str(c))
#     assert len(parser.generate_plc_configs()) == 0


# def test_generate_intermediate_yaml_plcs_empty(tmpdir, inp_data_fixture):
#     c = tmpdir.join("config.yaml")
#     cpa_file = tmpdir.join("test.yaml")
#     cpa_file.write("plcs: []")
#     c.write("cpa_file: test.yaml\ninp_file: input.inp")
#
#     inp_file = tmpdir.join("input.inp")
#     inp_file.write(inp_data_fixture)
#
#     parser = ConfigParser(str(c))
#     assert len(parser.generate_plc_configs()) == 0
#
#
# def test_generate_intermediate_yaml_plcs_normal(tmpdir, inp_data_fixture):
#     c = tmpdir.join("config.yaml")
#     cpa_file = tmpdir.join("test.yaml")
#     cpa_file.write("""plcs:
#   - name: PLC1
#     sensors:
#       - T1
#     actuators:
#       - P_RAW1
#       - V_PUB
#   - name: PLC2
#     sensors:
#       - T2
#       - T3
#     actuators:
#       - V_ER2i""")
#     c.write("cpa_file: test.yaml\ninp_file: input.inp")
#
#     inp_file = tmpdir.join("input.inp")
#     inp_file.write(inp_data_fixture)
#
#     parser = ConfigParser(str(c))
#     result = parser.generate_plc_configs()
#     assert len(result) == 2
#     # PLC 1
#     assert result[0].name == "PLC1"
#     assert result[0].sensors == ["T1"]
#     assert result[0].actuators == ["P_RAW1", "V_PUB"]
#     # Assert Correct Control parse
#     assert len(result[0].controls) == 1
#     assert result[0].controls[0].actuator == "V_PUB"
#     assert result[0].controls[0].action == "OPEN"
#     assert result[0].controls[0].dependant == "T1"
#     assert result[0].controls[0].value == 0.256
#     # PLC 2
#     assert result[1].name == "PLC2"
#     assert result[1].sensors == ["T2", "T3"]
#     assert result[1].actuators == ["V_ER2i"]
#     assert len(result[1].controls) == 1
#     assert result[1].controls[0].actuator == "V_ER2i"
#     assert result[1].controls[0].action == "CLOSED"
#     assert result[1].controls[0].value == 0
#
#
# def test_generate_intermediate_yaml_plcs_empty_sensor(tmpdir, inp_data_fixture):
#     c = tmpdir.join("config.yaml")
#     cpa_file = tmpdir.join("test.yaml")
#     cpa_file.write("""plcs:
#   - name: PLC1
#     sensors:
#     actuators:
#       - P_RAW1
#       - V_PUB""")
#     c.write("cpa_file: test.yaml\ninp_file: input.inp")
#
#     inp_file = tmpdir.join("input.inp")
#     inp_file.write(inp_data_fixture)
#
#     parser = ConfigParser(str(c))
#     result = parser.generate_plc_configs()
#     # PLC 1
#     assert result[0].name == "PLC1"
#     assert result[0].sensors == []
#     assert result[0].actuators == ["P_RAW1", "V_PUB"]
#     assert len(result[0].controls) == 1
#     assert result[0].controls[0].actuator == "V_PUB"
#     assert result[0].controls[0].action == "OPEN"
#     assert result[0].controls[0].dependant == "T1"
#     assert result[0].controls[0].value == 0.256
#
#
# def test_generate_intermediate_yaml_plcs_empty_actuator(tmpdir, inp_data_fixture):
#     c = tmpdir.join("config.yaml")
#     cpa_file = tmpdir.join("test.yaml")
#     cpa_file.write("""plcs:
#   - name: PLC1
#     sensors:
#       - T1
#     """)
#     c.write("cpa_file: test.yaml\ninp_file: input.inp")
#
#     inp_file = tmpdir.join("input.inp")
#     inp_file.write(inp_data_fixture)
#
#     parser = ConfigParser(str(c))
#     result = parser.generate_plc_configs()
#     # PLC 1
#     assert result[0].name == "PLC1"
#     assert result[0].sensors == ["T1"]
#     assert result[0].actuators == []
#     assert len(result[0].controls) == 0
