from dhalsim.parser.plc_config import PlcConfig
import pytest


@pytest.fixture
def config_fixture():
    return PlcConfig("TestPLC1", "xx‑xx‑xx‑xx‑xx‑xx", ["testSensor1", "testSensor2"],
                     ["testActuator1", "testActuator2"])


def test_name(config_fixture):
    assert config_fixture.name == "TestPLC1"


def test_mac(config_fixture):
    assert config_fixture.mac == "xx‑xx‑xx‑xx‑xx‑xx"


def test_sensor(config_fixture):
    assert config_fixture.sensors == ["testSensor1", "testSensor2"]


def test_actuator(config_fixture):
    assert config_fixture.actuators == ["testActuator1", "testActuator2"]

def test_mac(config_fixture):
    assert config_fixture.mac is None


def test_ip(config_fixture):
    assert config_fixture.ip is None