import sys

from dhalsim.parser.input_parser import InputParser

def test_python_version():
    assert sys.version_info.major is 3

def test_no_controls(tmpdir):
    c = tmpdir.join("input.inp")
    c.write("\n[CONTROLS]")
    parser = InputParser(str(tmpdir.join("input.inp")))
    controls = parser.generate_controls()
    assert len(controls) == 0


def test_single_node_control(tmpdir):
    c = tmpdir.join("input.inp")
    c.write("\n[CONTROLS]\nLINK V_PUB OPEN IF NODE T0 BELOW 0.256\n")
    parser = InputParser(str(tmpdir.join("input.inp")))
    controls = parser.generate_controls()
    assert len(controls) == 1
    control = controls[0]
    assert control.actuator == "V_PUB"
    assert control.action == "OPEN"
    assert control.dependant == "T0"
    assert control.value == 0.256


def test_single_node_and_time_control(tmpdir):
    c = tmpdir.join("input.inp")
    c.write("\n[CONTROLS]\nLINK V_PUB OPEN IF NODE T0 BELOW 0.256\nLINK P_RAW1 CLOSED AT TIME 0\n")
    parser = InputParser(str(tmpdir.join("input.inp")))
    controls = parser.generate_controls()
    assert len(controls) == 2
    node_control = controls[0]
    assert node_control.actuator == "V_PUB"
    assert node_control.action == "OPEN"
    assert node_control.dependant == "T0"
    assert node_control.value == 0.256
    time_control = controls[1]
    assert time_control.actuator == "P_RAW1"
    assert time_control.action == "CLOSED"
    assert time_control.value == 0
