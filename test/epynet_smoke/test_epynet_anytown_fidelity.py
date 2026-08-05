"""epynet fidelity test (C2) — tailored to anytown.

Reproduces anytown's INITIAL FILL PHASE with a standalone epynet run and asserts
the tank levels match the reference ground_truth.csv values produced by a real
288-iteration DHALSIM run.

Why only the fill phase (iterations 0..13):
  In anytown, both pumps (P78, P79) start OPEN and fill T41/T42 monotonically.
  The first control switch happens at iteration 14 (P78 CLOSES when T41 crosses
  its threshold). BEFORE that switch, nothing has actuated, so there is no PLC
  sync-delay effect — the trajectory is pure hydraulics and epynet must reproduce
  the full-DHALSIM ground truth closely. AFTER iteration 14, ground truth carries
  the cyber-layer overshoot (P78 cut at T41=8.63 rather than the control's 8.0),
  which a pure-epynet run cannot reproduce — that is the domain of the Tier-2
  full-pipeline golden-master test, not this one.

Reference values are the actual T41_LEVEL / T42_LEVEL columns from a real run.
Run:  python3 -m pytest test/epynet_smoke/test_epynet_anytown_fidelity.py -v
Needs compiled EPANET (epynet), NO root / NO Mininet -> Tier-1 lane.
"""
import os
import pytest

pytestmark = pytest.mark.integrationtest

epynet = pytest.importorskip("epynet")
from epynet.water_network import WaterDistributionNetwork
from epynet import epynetUtils

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INP = os.path.join(REPO, "examples", "anytown_topology", "anytown_map.inp")
# DHALSIM injects these demand multipliers (config: demand_patterns:
# demands_anytown_small.csv). The raw INP carries PAT1=1.0 (full demand), which
# drains the tanks; the injected "small" patterns (mean ~0.06) are what let the
# pumps fill them. Reproducing ground truth REQUIRES loading this file.
DEMANDS = os.path.join(REPO, "examples", "anytown_topology", "demands_anytown_small.csv")

PUMPS = ("P78", "P79")
# (iteration, T41_LEVEL, T42_LEVEL) from a real 288-iteration DHALSIM run,
# over the pre-control-switch fill window (both pumps open).
GROUND_TRUTH_PREFLIP = [
    (0, 3.0509999999999993, 3.0509999999999993),
    (1, 3.4954406549806474, 3.3748295538831594),
    (2, 3.9325375515923873, 3.698348784492125),
    (3, 4.362424699208565, 4.021444224947971),
    (4, 4.785228986269662, 4.344010191800022),
    (5, 5.201070061875811, 4.665948858748799),
    (6, 5.610088133855115, 4.987142877522522),
    (7, 6.012424747039635, 5.307474330776683),
    (8, 6.408213532097627, 5.626833756311226),
    (9, 6.7975825160277, 5.945117818180386),
    (10, 7.18065513402312, 6.262228266540562),
    (11, 7.55755081887109, 6.578071319315457),
    (12, 7.928385390881676, 6.892557244442616),
    (13, 8.30683717705087, 7.223009799204175),
]

# Tolerance: the fill window is pure hydraulics (no controls fired yet), so epynet
# should match DHALSIM's ground truth tightly. Loose enough to absorb solver
# build/platform float differences, tight enough to catch a real physics regression.
TOL = 0.01  # metres (observed match is exact to 4 dp)


def _make_processed_inp(src, dst):
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


def _level(state, tank):
    return state[tank]["pressure"]


def test_anytown_fill_phase_matches_ground_truth(tmp_path):
    pd = pytest.importorskip("pandas")
    assert os.path.exists(DEMANDS), f"missing demand file: {DEMANDS}"

    processed = str(tmp_path / "anytown_processed.inp")
    _make_processed_inp(INP, processed)
    net = WaterDistributionNetwork(processed)

    # mirror PhysicalPlant.set_initial_values(): inject the experiment's demand
    # multipliers for every pattern uid (physical_process.py line ~925)
    demands = pd.read_csv(DEMANDS)
    for pattern in net.patterns.uid:
        if pattern in demands:
            net.set_demand_pattern(pattern, demands[pattern].tolist())

    step = epynetUtils.get_time_parameter(
        net, epynetUtils.get_time_param_code("EN_HYDSTEP"))[1]
    net.set_time_params(duration=step * (len(GROUND_TRUTH_PREFLIP) + 2), hydraulic_step=step)
    net.init_simulation(interactive=True)

    # both pumps OPEN for the whole fill window (matches ground truth P78=P79=1)
    actuators = {p: 1 for p in PUMPS}

    # Iteration alignment: ground_truth row 0 is the INITIAL state (frozen
    # InitLevel), written by register_initial_results() BEFORE any step. The Nth
    # simulate_step() call therefore corresponds to ground-truth iteration N.
    curr = 0
    observed = {}
    for n in range(1, len(GROUND_TRUTH_PREFLIP) + 1):
        timestep, state = net.simulate_step(curr, actuators)
        observed[n] = (_level(state, "T41"), _level(state, "T42"))
        if timestep <= 0:
            break
        curr += timestep

    # compare against reference (skip iteration 0 = init condition, which is the
    # frozen InitLevel and not produced by a step)
    # Compare only over the pre-control-switch window. Ground-truth iteration 14 is
    # where P78 first CLOSES, and there the full pipeline shows the PLC sync-delay
    # overshoot (T41 cut at 8.63 vs the INP control's 8.0) which pure epynet cannot
    # reproduce — that divergence is the Tier-2 golden-master's territory.
    LAST_DETERMINISTIC_ITER = 13

    failures = []
    for it, ref_t41, ref_t42 in GROUND_TRUTH_PREFLIP:
        if it == 0 or it > LAST_DETERMINISTIC_ITER:
            continue
        if it not in observed:
            failures.append(f"iter {it}: no observation")
            continue
        obs_t41, obs_t42 = observed[it]
        if abs(obs_t41 - ref_t41) > TOL:
            failures.append(f"iter {it} T41: obs {obs_t41:.4f} vs ref {ref_t41:.4f} (d={abs(obs_t41-ref_t41):.4f})")
        if abs(obs_t42 - ref_t42) > TOL:
            failures.append(f"iter {it} T42: obs {obs_t42:.4f} vs ref {ref_t42:.4f} (d={abs(obs_t42-ref_t42):.4f})")

    assert not failures, "epynet fill-phase diverged from ground truth:\n  " + "\n  ".join(failures)
