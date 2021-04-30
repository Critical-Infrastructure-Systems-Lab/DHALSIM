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


# -- Bad Weather Tests -- #

def test_name_invalid():
    with pytest.raises(TypeError):
        PlcConfig(42, "xx‑xx‑xx‑xx‑xx‑xx", ["testSensor1", "testSensor2"],
                  ["testActuator1", "testActuator2"])


def test_mac_invalid():
    with pytest.raises(TypeError):
        PlcConfig("TestPLC1", 42, ["testSensor1", "testSensor2"],
                  ["testActuator1", "testActuator2"])


def test_sensor_invalid():
    with pytest.raises(TypeError):
        PlcConfig("TestPLC1", "xx‑xx‑xx‑xx‑xx‑xx", 42,
                  ["testActuator1", "testActuator2"])


def test_actuator_invalid():
    with pytest.raises(TypeError):
        PlcConfig("TestPLC1", "xx‑xx‑xx‑xx‑xx‑xx", ["testSensor1", "testSensor2"],
                  42)
