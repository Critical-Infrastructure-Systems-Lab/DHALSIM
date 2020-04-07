import wntr
import wntr.network.controls as controls
import sqlite3
import csv
import time

import sys

def get_node_list_by_type(list, type):
    result = []
    for node in list:
        if wn.get_node(node).node_type == type:
            result.append(str(node))
    return result


def get_link_list_by_type(list, type):
    result = []
    for link in list:
        if wn.get_link(link).link_type == type:
            result.append(str(link))
    return result


def create_node_header(list):
    result = []
    for node in list:
        result.append(node + "_LEVEL")
    return result


def create_link_header(list):
    result = []
    for link in list:
        result.append(link + "_FLOW")
        result.append(link + "_STATUS")
    return result


def get_controls(list):
    result = []
    for control in list:
        result.append(wn.get_control(control))
    return result


def create_control_dict(actuator):
    act_dict = dict.fromkeys(['actuator', 'parameter', 'value', 'condition', 'name'])
    act_dict['actuator'] = wn.get_link(actuator)
    act_dict['parameter'] = 'status'
    act_dict['condition'] = dummy_condition
    act_dict['name'] = actuator + "_control"
    if type(wn.get_link(actuator).status) is int:
        act_dict['value'] = act_dict['actuator'].status
    else:
        act_dict['value'] = act_dict['actuator'].status.value
    return act_dict


def register_results(results):
    values_list = []
    values_list.extend([results.timestamp])

    # Results are divided into: nodes: reservoir and tanks, links: flows and status
    # Get tanks levels
    for tank in tank_list:
        values_list.extend([wn.get_node(tank).level])

    # Get junction  levels
    for junction in junction_list:
        values_list.extend([wn.get_node(junction).head - wn.get_node(junction).elevation])

    # Get pumps flows and status
    for pump in pump_list:
        values_list.extend([wn.get_link(pump).flow])

        if type(wn.get_link(pump).status) is int:
            values_list.extend([wn.get_link(pump).status])
        else:
            values_list.extend([wn.get_link(pump).status.value])

            # Get valves flows and status
    for valve in valve_list:
        values_list.extend([wn.get_link(valve).flow])

        if type(wn.get_link(valve).status) is int:
            values_list.extend([wn.get_link(valve).status])
        else:
            values_list.extend([wn.get_link(valve).status.value])
    return values_list

def update_actuator_values():
    for actuator in control_list:
        update_actuator(actuator)

def update_actuator(actuator):
    rows_1 = c.execute("SELECT value FROM ctown WHERE name = actuator['name']").fetchall()
    conn.commit()

    new_status = rows_1[0][0]
    if new_status != actuator['value']:
        actuator['value'] = new_status

        #act1 = controls.ControlAction(pump1, 'status', int(pump1_status))
        new_action  = controls.ControlAction(control['actuator'], control['parameter'], control['value'])

        #pump1_control = controls.Control(condition, act1, name='pump1control')
        new_control = controls.Control(control['condition'], new_action, control['name'])

        wn.remove_control(actuator['name'])
        wn.add_control(actuator['name'], new_control)

# connection to the database
conn = sqlite3.connect('minitown_db.sqlite')
c = conn.cursor()

dummy_condition = controls.ValueCondition(wn.get_node('T1'), 'level', '>=', -1)

# Create the network
inp_file = sys.argv[2]+'_map.inp'
wn = wntr.network.WaterNetworkModel(inp_file)

# We define the simulation times in seconds
wn.options.time.duration = 1
wn.options.time.hydraulic_timestep = 5*60
wn.options.time.quality_timestep = 5*60
wn.options.time.pattern_timestep = 60*60
wn.options.time.report_timestep = 5*60

list_header = []
node_list = list(wn.node_name_list)
link_list = list(wn.link_name_list)

#reservoir_list = get_node_list_by_type(node_list, 'Reservoir')
tank_list      = get_node_list_by_type(node_list, 'Tank')
junction_list  = get_node_list_by_type(node_list, 'Junction')
pump_list      = get_link_list_by_type(link_list, 'Pump')
valve_list     = get_link_list_by_type(link_list, 'Valve')
#control_names  = wn.control_name_list

list_header = ["Timestamps"]
aux = create_node_header(tank_list)
list_header.extend(aux)

aux = create_node_header(junction_list)
list_header.extend(aux)

aux = create_link_header(pump_list)
list_header.extend(aux)

aux = create_link_header(valve_list)
list_header.extend(aux)

results_list = []
results_list.append(list_header)

#control_list_str = get_controls(control_names)

control_list = []
for valve in valve_list:
    control_list.append(create_control_dict(valve))

for pump in pump_list:
    control_list.append(create_control_dict(pump))


for control in control_list:
    #act1 = controls.ControlAction(pump1, 'status', int(pump1_status))
    an_action = controls.ControlAction(control['actuator'], control['parameter'], control['value'])
    a_control = controls.Control(control['condition'], an_action, control['name'])
    wn.add_control(control['name'], a_control)

if sys.argv[1] == 'pdd':
    print('Running simulation using PDD')
    sim = wntr.sim.WNTRSimulator(wn, mode='PDD')
elif sys.argv[1] == 'dd':
    print('Running simulation using DD')
    sim = wntr.sim.WNTRSimulator(wn)
else:
    print('Invalid simulation mode, exiting...')
    sys.exit(1)

master_time = 0
days = 1
iteration_limit = (days*24*3600)/wn.options.time.hydraulic_timestep

while master_time <= iteration_limit:

    #update_actuator_values()

    results = sim.run_sim(convergence_error=True)
    values_list = register_results(results)

    results_list.append(values_list)
    master_time += 1