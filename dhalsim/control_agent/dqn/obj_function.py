def supply_demand_ratio(supplies, base_demands):
    """
    Compute the DSR at the end of the simulation for each time step controlled.
    # TODO: can be retrieved from saved_values in scada?

    :param supplies: list of junctions actual demand for each time step of the simulation (list of list)
    :type supplies: list

    :param base_demands: list of junctions base demand for each time step of the simulation (list of list)
    :type base_demands:list

    :return: average over all the ratios (actual_demand / base_demand)
    """
    ratios = []

    for junc in range(len(supplies[0])):
        junc_supply = sum([timestep[junc] for timestep in supplies])
        junc_demand = sum([timestep[junc] for timestep in base_demands])

        if junc_demand > 0:
            ratios.append(junc_supply / junc_demand if junc_supply / junc_demand <= 1 else float(1))
        else:
            ratios.append(float(0))

    return sum(ratios) / len(ratios)


def step_supply_demand_ratio(supplies, base_demands):
    """
    Compute DSR for the current step.

    :param supplies: current step junctions actual demand
    :type supplies: list

    :param base_demands: current step junctions base demand
    :type base_demands: list

    :return: ratio betweeen step actual_demands and base_demands
    """
    tot_supply = sum(supplies)
    tot_demand = sum(base_demands)

    if tot_demand == 0:
        return 0
    else:
        return tot_supply / tot_demand if tot_supply / tot_demand <= 1 else float(1)


def fake_obj_funtion():
    return 0.9

