"""Standalone epynet smoke test — exercises DHALSIM's two epynet integration points
(read tank/sensor values; write pump status + step) WITHOUT Mininet, PLCs, the
sync-flag handshake, or the SQLite DB.

Read/write surfaces verified against DHALSIM's own physical_process.py and a real
288-iteration anytown run (ground_truth.csv):

  * The LIVE tank level is the EPANET node PRESSURE, read from the state dict
    returned by simulate_step:  state[tank]['pressure']   (this is what
    register_results() writes to ground_truth.csv as "<tank>_LEVEL").
  * `.tanklevel` / `.results['level']` are FROZEN at the INP InitLevel (3.051 for
    anytown) — they are the initial-condition surface, NOT the live value. Reading
    them per-step was the classic trap.
  * Stepping follows EPANET's ENrunH/ENnextH: advance curr_time by the RETURNED
    timestep, loop while timestep > 0 (mirrors PhysicalPlant.simulate_with_epynet).

anytown control coupling (from map.inp [CONTROLS], stripped for the epynet path
and driven externally): P78 fills T41, P79 fills T42.

Run:  python3 -m pytest test/epynet_smoke -v
Needs compiled EPANET (epynet) but NO root / NO Mininet -> Tier-1 lane.
"""
import os
import pytest

pytestmark = pytest.mark.integrationtest

epynet = pytest.importorskip("epynet")
from epynet.water_network import WaterDistributionNetwork
from epynet import epynetUtils

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INP = os.path.join(REPO, "examples", "anytown_topology", "anytown_map.inp")

# real coupled pairs from anytown [CONTROLS]
PUMP, TANK = "P78", "T41"


def _make_processed_inp(src, dst):
    """Strip [CONTROLS], mirroring PhysicalPlant.remove_controls_from_inp_file."""
    write_out = True
    with open(src) as infile, open(dst, "w") as outfile:
        for line in infile:
            if write_out:
                outfile.write(line)
            if line.startswith("[CONTROLS]"):
                write_out = False
                continue
            if not write_out and line.startswith("["):
                write_out = True
                outfile.write(line)


def _new_network(tmp_path, duration_steps=300):
    processed = str(tmp_path / "anytown_processed.inp")
    _make_processed_inp(INP, processed)
    net = WaterDistributionNetwork(processed)
    step = epynetUtils.get_time_parameter(
        net, epynetUtils.get_time_param_code("EN_HYDSTEP"))[1]
    net.set_time_params(duration=step * duration_steps, hydraulic_step=step)
    net.init_simulation(interactive=True)
    return net, step


def _tank_level(state, tank):
    """Live tank level = node pressure in the returned state dict (what DHALSIM writes)."""
    return state[tank]["pressure"]


def _run(net, n_events, actuators=None):
    """Advance up to n_events using EPANET's returned timestep. Return final state dict."""
    curr, state = 0, None
    for _ in range(n_events):
        timestep, state = net.simulate_step(curr, actuators)
        if timestep <= 0:
            break
        curr += timestep
    return state


def test_state_dict_is_indexed_by_element(tmp_path):
    """get_network_state() is a Series keyed by uid; tanks carry {'pressure'}."""
    net, _ = _new_network(tmp_path)
    state = _run(net, n_events=3)
    assert TANK in state, f"{TANK} not in state index: {list(state.index)[:8]}"
    assert "pressure" in state[TANK]
    assert PUMP in state and "status" in state[PUMP] and "flow" in state[PUMP]


def test_read_integration_point(tmp_path):
    """READ: live tank level (pressure) and pump flow are readable and sane."""
    net, _ = _new_network(tmp_path)
    state = _run(net, n_events=3)
    level = _tank_level(state, TANK)
    flow = state[PUMP]["flow"]
    assert isinstance(level, (int, float))
    assert isinstance(flow, (int, float))


def test_live_level_differs_from_init_accessor(tmp_path):
    """The live level (pressure) must diverge from the frozen .tanklevel init value.
    Guards against the exact bug this test was written to catch."""
    net, _ = _new_network(tmp_path)
    init_accessor = net.tanks[TANK].tanklevel        # frozen InitLevel (3.051)
    state = _run(net, n_events=30)
    live = _tank_level(state, TANK)
    assert live != init_accessor, (
        f"live level {live} == init accessor {init_accessor} — reading the frozen "
        "InitLevel surface instead of the stepped state"
    )


def test_write_integration_point_reaches_physics(tmp_path):
    """WRITE + STEP: forcing pump status changes pump FLOW (actuation reaches physics).

    Flow is the direct, unambiguous signal of the write integration point: a
    real 288-iteration probe shows P78 pumping ~500+ units when OPEN and exactly
    0 when CLOSED. (Tank *level* is a poor signal here — anytown demand drains
    T41 to its MinLevel=0 floor within ~6 steps regardless of pump status, so the
    pump feeds the network without holding the tank up. Asserting on level would
    be physically ill-posed for this topology.)"""
    net_open, _ = _new_network(tmp_path)
    state_open = _run(net_open, n_events=3, actuators={PUMP: 1})    # 1 = OPEN
    flow_open = state_open[PUMP]["flow"]
    status_open = state_open[PUMP]["status"]

    net_closed, _ = _new_network(tmp_path)
    state_closed = _run(net_closed, n_events=3, actuators={PUMP: 0})  # 0 = CLOSED
    flow_closed = state_closed[PUMP]["flow"]
    status_closed = state_closed[PUMP]["status"]

    # the status command took effect
    assert status_open == 1 and status_closed == 0, (
        f"pump status not applied: OPEN->{status_open} CLOSED->{status_closed}"
    )
    # and it reached the hydraulics: flow when open, none when closed
    assert flow_open > 0, f"pump OPEN but flow={flow_open} (actuation not reaching physics)"
    assert flow_closed == 0, f"pump CLOSED but flow={flow_closed} (status not honored)"
