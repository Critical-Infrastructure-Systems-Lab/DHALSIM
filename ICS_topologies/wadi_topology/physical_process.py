import wntr
import wntr.network.controls as controls
import sqlite3
import csv
import time
import pandas as pd
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
    act_dict['name'] = actuator
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

    # For some reason WADI does not support junctions properly - Get junction  levels
    #for junction in junction_list:
    #values_list.extend([wn.get_node(junction).head - wn.get_node(junction).elevation])

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

    rows = c.execute("SELECT value FROM wadi WHERE name = 'ATT_1'").fetchall()
    conn.commit()
    attack1 = int(rows[0][0])

    rows = c.execute("SELECT value FROM wadi WHERE name = 'ATT_2'").fetchall()
    conn.commit()
    attack2 = int(rows[0][0])

    values_list.extend([attack1, attack2])
    return values_list

def update_controls():
    for control in control_list:
        update_control(control)

def update_control(control):
    act_name = '\'' + control['name'] + '\''
    rows_1 = c.execute('SELECT value FROM wadi WHERE name = ' + act_name).fetchall()
    conn.commit()
    new_status = int(rows_1[0][0])

    control['value'] = new_status

    #act1 = controls.ControlAction(pump1, 'status', int(pump1_status))
    new_action  = controls.ControlAction(control['actuator'], control['parameter'], control['value'])

    #pump1_control = controls.Control(condition, act1, name='pump1control')
    new_control = controls.Control(control['condition'], new_action, name=control['name'])

    wn.remove_control(control['name'])
    wn.add_control(control['name'], new_control)

def write_results(results):
    with open('output/'+sys.argv[3], 'w', newline='\n') as f:
        writer = csv.writer(f)
        writer.writerows(results)

# connection to the database
conn = sqlite3.connect('wadi_db.sqlite')
c = conn.cursor()


# Create the network
inp_file = sys.argv[2]+'_map.inp'
wn = wntr.network.WaterNetworkModel(inp_file)

dummy_condition = controls.ValueCondition(wn.get_node('T0'), 'level', '>=', -1)
list_header = []
node_list = list(wn.node_name_list)
link_list = list(wn.link_name_list)

#reservoir_list = get_node_list_by_type(node_list, 'Reservoir')
tank_list = get_node_list_by_type(node_list, 'Tank')
pump_list = get_link_list_by_type(link_list, 'Pump')
valve_list = get_link_list_by_type(link_list, 'Valve')

list_header = ["Timestamps"]
aux = create_node_header(tank_list)
list_header.extend(aux)

aux = create_link_header(pump_list)
list_header.extend(aux)

aux = create_link_header(valve_list)
list_header.extend(aux)

list_header.extend(["Attack#01", "Attack#02"])

results_list = []
results_list.append(list_header)


control_list = []
for valve in valve_list:
    control_list.append(create_control_dict(valve))

for pump in pump_list:
    control_list.append(create_control_dict(pump))

for control in control_list:
    an_action = controls.ControlAction(control['actuator'], control['parameter'], control['value'])
    a_control = controls.Control(control['condition'], an_action, name=control['name'])
    wn.add_control(control['name'], a_control)

if sys.argv[1] == 'pdd':
    sim = wntr.sim.WNTRSimulator(wn, mode='PDD')
elif sys.argv[1] == 'dd':
    print('Running simulation using DD')
    sim = wntr.sim.EpanetSimulator(wn)
else:
    print('Invalid simulation mode, exiting...')
    sys.exit(1)


sim.run_sim()
master_time = 0
iteration_limit = (14*60)    #14 hours

while master_time <= iteration_limit:

    update_controls()
    print("ITERATION %d ------------- " % master_time)
    results = sim.run_sim()
    values_list = register_results(results)
    results_list.append(values_list)
    master_time += 1

    for tank in tank_list:
        tank_name = '\'' + tank + '\''
        a_level = wn.get_node(tank).level
        query = "UPDATE wadi SET value = " + str(a_level) + " WHERE name = " + tank_name
        c.execute(query)  # UPDATE TANKS IN THE DATABASE
        conn.commit()

write_results(results_list)