import sys
from dhalsim.physical_process import PhysicalPlant
from mock import patch
from wntr.network import WaterNetworkModel
from wntr.sim import WNTRSimulator
from pytest import raises


# TODO:
# test other classes in physical_process.py

def get_physical_plant(test_args=[0, '../test/auxilary_testing_files/wadi_config.yaml', 1, False]):
    with patch.object(sys, 'argv', test_args):
        return PhysicalPlant()


def test_week_index():
    assert get_physical_plant().week_index == 0


def test_attack_flag():
    assert get_physical_plant().attack_flag == False


def test_attack_path():
    with raises(AttributeError):
        return get_physical_plant().attack_path


def test_attack_name():
    with raises(AttributeError):
        return get_physical_plant().attack_name


def test_db_path():
    assert get_physical_plant().db_path == 'wadi_db.sqlite'


def test_conn():
    assert get_physical_plant().conn is not None


def test_c():
    assert get_physical_plant().c is not None


def test_output_path():
    assert get_physical_plant().output_path == 'physical_process.csv'


def test_simulation_days():
    assert get_physical_plant().simulation_days == 1


def test_wn():
    assert isinstance(get_physical_plant().wn, WaterNetworkModel)


def test_node_list():
    # Node_list corresponds to [COORDINATES] section of inp file
    assert len(get_physical_plant().node_list) == 79
    assert get_physical_plant().node_list[0] == 'J_CT3'


def test_link_list():
    # link_list corresponds to [PIPES], [PUMPS] and [VALVES] sections of inp file
    assert len(get_physical_plant().link_list) == 82
    assert get_physical_plant().link_list[0] == 'p1_RWP1in'
    assert get_physical_plant().link_list[56] == 'P_RAW1'
    assert get_physical_plant().link_list[60] == 'V_Gi_G'


def test_tank_list():
    assert len(get_physical_plant().tank_list) == 3
    assert get_physical_plant().tank_list[0] == 'T1'


def test_junction_list():
    assert len(get_physical_plant().junction_list) == 74
    assert get_physical_plant().junction_list[0] == 'J_CT3'


def test_pump_list():
    assert len(get_physical_plant().pump_list) == 4
    assert get_physical_plant().pump_list[0] == 'P_RAW1'


def test_valve_list():
    assert len(get_physical_plant().valve_list) == 22
    assert get_physical_plant().valve_list[0] == 'V_Gi_G'


# TODO
# def test_attack_start():

# TODO
# def test_attack_end():

def test_results_list():
    # create_link_header produces two extra entries, create_node_header produces one extra entry:
    # 1 * 3 + 1 * 74 + 2 * 4 + 2 * 4 + 2 * 22 = 137.
    # Including ["Timestamps"], ["Attack#01"] and ["Attack#02"] we get 137 + 3 = 140.
    print(get_physical_plant().results_list)
    assert len(get_physical_plant().results_list) == 1
    assert len(get_physical_plant().results_list[0]) == 140


def test_control_list():
    # Length is equal to number of pumps and valves. Test is dependent on other tests.
    assert len(get_physical_plant().control_list) == 26


def test_demand_model():
    # WNTR converts value 'pdd' as seen in inp file to 'PDA' @dhalsim.options.py
    assert get_physical_plant().wn.options.hydraulic.demand_model == 'PDA'


def test_sim():
    assert isinstance(get_physical_plant().sim, WNTRSimulator)
