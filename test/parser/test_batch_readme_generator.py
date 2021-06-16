from datetime import datetime
from pathlib import Path

import pytest
from mock import patch
from wntr.network import WaterNetworkModel, Options

from dhalsim.parser.file_generator import BatchReadmeGenerator


@pytest.fixture
def batch_gen(mocker):
    mocker.patch.object(BatchReadmeGenerator, "__init__", return_value=None)

    return BatchReadmeGenerator(None)


@pytest.fixture
def water_network_model(mocker):
    wn = mocker.patch.object(WaterNetworkModel, "__init__", return_value=None)
    opts = mocker.patch.object(Options, "__init__", return_value=None)
    opts.time.hydraulic_timestep = 100
    wn.options = opts
    return wn


@pytest.fixture(scope="session")
def tmp_path(tmpdir_factory):
    return tmpdir_factory.mktemp("data").join("batch_readme.md")


def test_init(water_network_model):
    batch_rm_gen = BatchReadmeGenerator(Path(__file__).parent.parent / 'auxilary_testing_files'
                                        / 'intermediate.yaml', Path('../readme.md'),
                                        datetime(year=2021, month=6, day=1, second=1),
                                        datetime(year=2021, month=6, day=1, second=2),
                                        water_network_model, 5)
    assert batch_rm_gen.readme_path == Path('../readme.md')
    assert batch_rm_gen.start_time == datetime(year=2021, month=6, day=1, second=1)
    assert batch_rm_gen.end_time == datetime(year=2021, month=6, day=1, second=2)
    assert batch_rm_gen.wn == water_network_model
    assert batch_rm_gen.master_time == 5


def test_get_batch_information(batch_gen):
    batch_gen.intermediate_yaml = {'inp_file': 'mymap.inp', 'batch_index': 0,
                                   'batch_simulations': 2}
    assert batch_gen.get_batch_information() == "# Auto-generated README of mymap for batch" \
                                                " 1\n\nThis is batch 1 out of 2."


def test_get_initial_tank_values(batch_gen):
    batch_gen.intermediate_yaml = {'initial_tank_values': {'T2': 2.08023668123243}}
    assert batch_gen.get_initial_tank_values() == "\n\n## Initial tank data" \
                                                  "\n\n{'T2': 2.08023668123243}"


def test_get_network_loss_value(batch_gen):
    batch_gen.intermediate_yaml = {'network_loss_values': {'PLC1': 0.1427168730880501,
                                                           'PLC2': 0.2708496621297529,
                                                           'scada': 0.1649651164870355}}
    assert batch_gen.get_network_loss_value() == "\n\n## Network loss values\n\n" \
                                                 "{'PLC1': 0.1427168730880501, 'PLC2':" \
                                                 " 0.2708496621297529, 'scada': 0.1649651164870355}"


def test_get_network_delay_values(batch_gen):
    batch_gen.intermediate_yaml = {'network_delay_values': {'PLC1': '89.55084013904876ms',
                                                            'PLC2': '46.17408713948684ms',
                                                            'scada': '4.134693808027478ms'}}
    assert batch_gen.get_network_delay_values() == "\n\n## Network delay values\n\n{'PLC1':" \
                                                   " '89.55084013904876ms', 'PLC2': '46.17408713948684ms'," \
                                                   " 'scada': '4.134693808027478ms'}"


def test_get_time_information(batch_gen, water_network_model):
    batch_gen.master_time = 1
    batch_gen.intermediate_yaml = {'iterations': 4}

    water_network_model.options.time.hydraulic_timestep = 100
    batch_gen.wn = water_network_model
    batch_gen.start_time = datetime(year=2021, month=6, day=1, second=1)
    batch_gen.end_time = datetime(year=2021, month=6, day=1, second=2)
    assert batch_gen.get_time_information() == "\n\n## Information about this batch\n\nRan for 1 " \
                                               "out of 4 iterations with hydraulic timestep 100." \
                                               "\n\nStarted at 2021-06-01 00:00:01 and finished at " \
                                               "2021-06-01 00:00:02.\n\nThe duration of this batch was" \
                                               " 0:00:01."


def test_verify_written(batch_gen, tmp_path, water_network_model):
    batch_gen.readme_path = tmp_path
    batch_gen.start_time = datetime(year=2021, month=6, day=1, second=1)
    batch_gen.end_time = datetime(year=2021, month=6, day=1, second=2)
    batch_gen.wn = water_network_model
    batch_gen.master_time = 1
    batch_gen.intermediate_yaml = {'inp_file': 'my_map.inp', 'batch_index': 0,
                                   'batch_simulations': 2, 'iterations': 3}

    batch_gen.write_batch()

    open(tmp_path, 'r')

