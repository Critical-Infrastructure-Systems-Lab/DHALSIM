from datetime import datetime
from pathlib import Path

import pytest
from wntr.network import WaterNetworkModel, Options

from dhalsim.parser.file_generator import GeneralReadmeGenerator


@pytest.fixture
def rm_gen(mocker):
    mocker.patch.object(GeneralReadmeGenerator, "__init__", return_value=None)

    return GeneralReadmeGenerator(None)


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


def test_get_value(rm_gen):
    rm_gen.intermediate_yaml = {'parameter': 'value'}
    assert rm_gen.get_value('parameter') == "\n\nparameter: value"


def test_get_optional_present(rm_gen):
    rm_gen.intermediate_yaml = {'parameter': 'value'}
    assert rm_gen.get_optional('parameter') == "\n\nparameter: value"


def test_get_optional_absent(rm_gen):
    rm_gen.intermediate_yaml = {'parameter': 'value'}
    assert rm_gen.get_optional('unexisting') == "\n\nunexisting: None"


def test_checkbox_positive(rm_gen):
    rm_gen.intermediate_yaml = {'parameter': {'T2': 2.08023668123243}}
    assert rm_gen.checkbox('parameter') == "\n\n- [x] parameter"


def test_checkbox_negative(rm_gen):
    rm_gen.intermediate_yaml = {'parameter': {}}
    assert rm_gen.checkbox('parameter') == "\n\n- [ ] parameter"


def test_checkbox_absent(rm_gen):
    rm_gen.intermediate_yaml = {}
    assert rm_gen.checkbox('parameter') == "\n\n- [ ] parameter"


# todo
def test_get_readme_path(rm_gen):
    assert True


def test_get_input_files_w_batch(rm_gen):
    rm_gen.intermediate_yaml = {'batch_simulations': 3,
                                'output_path': Path('tmp/readme/batch0')}
    assert rm_gen.get_input_files() == "\n\n## Input files\n\nInput files have been copied to" \
                                       " ```tmp/readme```. In case any extra files were used," \
                                       " these files will be copied to the /output/configuration" \
                                       " folder as well."


def test_get_input_files_wo_batch(rm_gen):
    rm_gen.intermediate_yaml = {'output_path': Path('tmp/readme')}
    assert rm_gen.get_input_files() == "\n\n## Input files\n\nInput files have been copied to" \
                                       " ```tmp/readme```. In case any extra files were used," \
                                       " these files will be copied to the /output/configuration" \
                                       " folder as well."


def test_get_configuration_parameters(rm_gen):
    rm_gen.intermediate_yaml = {'iterations': 1, 'network_topology_type': 'Simple',
                                'mininet_cli': False, 'log_level': 'info', 'simulator': 'pdd'}
    assert rm_gen.get_configuration_parameters() == "\n\n## Configuration parameters\n\niterations:" \
                                                    " 1\n\nnetwork_topology_type: Simple\n\n" \
                                                    "mininet_cli: False\n\nlog_level: info\n\n" \
                                                    "simulator: pdd\n\nbatch_simulations: None"

# TODO