from dhalsim.static.plc_config import PlcConfig
import pytest


@pytest.fixture
def control_list_fixture():
    return [TimeControl("testActuator1", "CLOSED", 5), BelowControl("testActuator1", "CLOSED", "testSensor2", 5)]


@pytest.fixture
def config_fixture(control_list_fixture):
    return PlcConfig(name="TestPLC1", sensors=["testSensor1", "testSensor2"],
                     actuators=["testActuator1", "testActuator2"], mac="12:34:56:78:9A:BC",
                     ip="123.456.789.123", db_path="./the_path.sqlite", db_name="plc1")


def test_name(config_fixture):
    assert config_fixture.name == "TestPLC1"


def test_sensor(config_fixture):
    assert config_fixture.sensors == ["testSensor1", "testSensor2"]


def test_actuator(config_fixture):
    assert config_fixture.actuators == ["testActuator1", "testActuator2"]


def test_mac(config_fixture):
    assert config_fixture.mac is "12:34:56:78:9A:BC"


def test_controls(config_fixture, control_list_fixture):
    assert config_fixture.controls == control_list_fixture


def test_ip(config_fixture):
    assert config_fixture.ip is "123.456.789.123"


def test_db_path(config_fixture):
    assert config_fixture.db_path is "./the_path.sqlite"


def test_db_name(config_fixture):
    assert config_fixture.db_name is "plc1"


def test_tags(config_fixture):
    assert all(elem in config_fixture.tags for elem in [
        ('testSensor1', 1, 'REAL'),
        ("testSensor2", 1, 'REAL'),
        ("testActuator2", 1, 'REAL'),
        ("testActuator1", 1, 'REAL')])
    assert len(config_fixture.tags) is 4


def test_server(config_fixture):
    assert config_fixture.server["address"] is "123.456.789.123"
    assert all(elem in config_fixture.server["tags"] for elem in [
        ('testSensor1', 1, 'REAL'),
        ("testActuator1", 1, 'REAL'),
        ("testSensor2", 1, 'REAL'),
        ("testActuator2", 1, 'REAL')])
    assert len(config_fixture.server["tags"]) is 4


def test_protocol(config_fixture):
    assert config_fixture.protocol["name"] is "enip"
    assert config_fixture.protocol["mode"] is 1
    assert config_fixture.protocol["server"]["address"] is "123.456.789.123"
    assert all(elem in config_fixture.protocol["server"]["tags"] for elem in [
        ("testActuator1", 1, 'REAL'),
        ("testSensor2", 1, 'REAL'),
        ('testSensor1', 1, 'REAL'),
        ("testActuator2", 1, 'REAL')])
    assert len(config_fixture.protocol["server"]["tags"]) is 4


def test_state(config_fixture):
    assert config_fixture.state["name"] is "plc1"
    assert config_fixture.state["path"] is "./the_path.sqlite"
