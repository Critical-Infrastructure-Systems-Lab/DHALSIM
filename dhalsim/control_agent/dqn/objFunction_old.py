from . import network
import datetime


def flow_demand_ratio(wds: network.WaterDistributionNetwork, driven_links):
    """
    Computes the ratio between the total delivered and total requested water
    :param wds: network we are working on
    :param driven_links: actuators list
    :return: the objective function value
    """
    if not wds.solved:
        raise Exception("Simulation not completed!")

    # TODO: check if we need actually the demand or something else
    tot_requested = sum([wds.df_nodes_report['junctions', junc_id, 'demand'].sum() for junc_id in wds.junctions.uid])
    tot_delivered = sum([wds.df_links_report['pumps', link_id, 'flow'].sum() for link_id in driven_links])

    ratio = tot_delivered / tot_requested
    return ratio


def step_flow_demand_ratio(wds: network.WaterDistributionNetwork, driven_links):
    """
    Computes the ratio between the delivered and requested water at each step and average it, without considering the
    first two iterations which only stabilize the network
    :param wds: network we are working on
    :param driven_links: actuators list
    :return: the objective function value
    """
    if not wds.solved:
        raise Exception("Simulation not completed!")

    ratios = []
    demands = []
    flows = []

    for time in wds.df_links_report.index:
        demand = sum([wds.df_nodes_report.loc[time]['junctions', junc_id, 'demand'] for junc_id in wds.junctions.uid])
        flow = sum([wds.df_links_report.loc[time]['pumps', pump_id, 'flow'] for pump_id in driven_links])
        demands.append(demand)
        flows.append(flow)
        ratios.append(flow / demand)
    print('flows    : ' + str(flows))
    print('demands  : ' + str(demands))
    print('ratios   : ' + str(ratios))
    # print(ratios[2:])
    # print(sum(ratios[2:]) / (len(ratios) - 2))
    return sum(ratios[2:]) / (len(ratios) - 2)


def average_demand_deficit(wds: network.WaterDistributionNetwork, target_junctions=None):
    """
    Minimize the average demand deficit at each step, so I get an averaged value of how big is the demand deficit at
    each iteration
    :param wds: network we are working on
    :param target_junctions: junctions to consider for the computation of the objective function
    :return: the objective function value
    """
    if not wds.solved:
        raise Exception("Simulation not completed!")

    if target_junctions:
        demand_deficit = sum([wds.junctions[junc_id].demand_deficit.sum() for junc_id in target_junctions])
    else:
        demand_deficit = sum(wds.junctions.demand_deficit.sum())

    result = demand_deficit / len(wds.times)
    return result


def supply_demand_ratio(wds: network.WaterDistributionNetwork, target_junctions=None):
    """
    Computes the actual demand / basedemand ratio at each timestep and then it averages among all the ratios collected
    so far.
    :param wds: network we are working on
    :param target_junctions: junctions to consider for the computation of the objective function
    :return: the objective function value
    """
    if not wds.solved:
        raise Exception("Simulation not completed!")

    ratios = []

    if target_junctions:
        for i, time in enumerate(wds.times):
            actual_demand = sum([wds.junctions[junc_id].actual_demand.loc[time] for junc_id in target_junctions ])
            basedemand = sum([wds.junctions[junc_id].results['basedemand'][i] for junc_id in target_junctions])
            ratios.append(actual_demand/basedemand if actual_demand/basedemand <= 1 else float(1))
    else:
        for i, time in enumerate(wds.times):
            actual_demand = wds.junctions.actual_demand.loc[time].sum()
            basedemand = sum([wds.junctions[junc_id].results['basedemand'][i] for junc_id in wds.junctions.uid])
            ratios.append(actual_demand/basedemand if actual_demand/basedemand <= 1 else float(1))
            
    return sum(ratios) / len(ratios)


def step_supply_demand_ratio(wds: network.WaterDistributionNetwork, target_junctions=None):
    """

    :param wds:
    :param target_junctions:
    :return:
    """
    ratios = []

    if target_junctions:
        actual_demand = sum([wds.junctions[junc_id].actual_demand.iloc[-1] for junc_id in target_junctions])
        basedemand = sum([wds.junctions[junc_id].results['basedemand'][-1] for junc_id in target_junctions])
        ratios.append(actual_demand / basedemand if actual_demand / basedemand <= 1 else float(1))
    else:
        actual_demand = wds.junctions.actual_demand.iloc[-1].sum()
        basedemand = sum([wds.junctions[junc_id].results['basedemand'][-1] for junc_id in wds.junctions.uid])
        ratios.append(actual_demand / basedemand if actual_demand / basedemand <= 1 else float(1))

    return sum(ratios) / len(ratios)


def pressure_violations(wds: network.WaterDistributionNetwork, target_nodes, nodes_band):
    """
    Computes how many pressure violations there have been at the end of the simulation
    :param wds: network we are working on
    :param target_nodes: list of ids of nodes to check
    :param nodes_band: dictionary for each node_id with a tuple of min/max bounds -> {'id': [min, max]}
    :return: number of violations (negative because we maximize)
    """
    if not wds.solved:
        raise Exception("Simulation not completed!")

    n_violations = 0

    for node_id in target_nodes:
        node_bools = (wds.junctions[node_id].pressure < nodes_band[node_id][0]) | \
                     (wds.junctions[node_id].pressure > nodes_band[node_id][1])
        n_violations += node_bools.sum()

    return -n_violations


def energy_consumption(wds: network.WaterDistributionNetwork):
    """
    Computes the total energy consumption at the end of the simulation
    :param wds: network object
    :return: total energy consumed in the current simulation
    """
    if not wds.solved:
        raise Exception("Simulation not completed!")

    total_energy = wds.pumps.energy.values.sum()
    return total_energy


def tanks_feed_ratio(wds: network.WaterDistributionNetwork):
    """
    Computes the ratio between (junctions_demand) / (junctions_demand + total_tanks_flow), where the total_tanks_flow
    is determined by the sum of the absolute value of inflow and outflow for every tank.
    The objective function is taken from: https://github.com/BME-SmartLab/rl-wds
    :param wds: network object
    :return: feed ratio of the current simulation
    """
    if not wds.solved:
        raise Exception("Simulation not completed!")

    # TODO: understand if it makes sense to be used for the whole simulation as in DE and not only online (PROBABLY NOT)
    total_feed_ratio = 0
    # Transform wds.times (which are in seconds) to timedelta values
    times = [datetime.timedelta(seconds=time) for time in wds.times]
    for time in times:
        total_demand = sum([wds.df_nodes_report.loc[time]['junctions', junc_id, 'demand'] for junc_id in wds.junctions.uid])
        # TODO: problem with inflow-outflow and step-by-step simulation
        # total_tank_flow = sum([tank.inflow + tank.outflow for tank in wds.tanks])
        # total_feed_ratio += total_demand / (total_demand  + total_tank_flow)
    return total_feed_ratio
