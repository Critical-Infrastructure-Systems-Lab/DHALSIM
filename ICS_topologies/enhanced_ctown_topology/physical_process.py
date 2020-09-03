import wntr
import wntr.network.controls as controls
import sqlite3
import csv
import time
from datetime import datetime
import sys
import pandas as pd

################################ Weekly or Ten Days Simulation ###############################################
WEEKLY = False

def initialize_tanks_and_actuators():
    loaded_values = pd.read_csv('last_values.csv')

    for tank in tank_list:
        wn.get_node(tank).init_level = float(loaded_values.iloc[0][tank])

    for pump in pump_list:
        wn.get_link(pump).status = float(loaded_values.iloc[0][pump])

    for valve in valve_list:
        wn.get_link(valve).status = float(loaded_values.iloc[0][valve])

def initialize_simulation():

    if WEEKLY:
        limit = 167
    else:
        limit = 239

    print("Running simulation with week index: " + str(week_index))
    total_demands = pd.read_csv('../../Demand_patterns/three_year_demands_ctown.csv', index_col=0)
    demand_starting_points = pd.read_csv('../../Demand_patterns/starting_demand_points.csv', index_col=0)
    initial_tank_levels = pd.read_csv('../../Demand_patterns/tank_initial_conditions.csv', index_col=0)
    week_start = demand_starting_points.iloc[week_index][0]
    week_demands = total_demands.loc[week_start:week_start + limit, :]

    for name, pat in wn.patterns():
        pat.multipliers = week_demands[name].values.tolist()

    for i in range(1,8):
        wn.get_node('T' + str(i)).init_level = float(initial_tank_levels.iloc[week_index]['T'+ str(i)])

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

    rows = c.execute("SELECT value FROM ctown WHERE name = 'ATT_1'").fetchall()
    conn.commit()
    attack1 = int(rows[0][0])

    rows = c.execute("SELECT value FROM ctown WHERE name = 'ATT_2'").fetchall()
    conn.commit()
    attack2 = int(rows[0][0])

    values_list.extend([attack1, attack2])
    return values_list

def update_controls():
    for control in control_list:
        update_control(control)

def update_control(control):
    act_name = '\'' + control['name'] + '\''
    rows_1 = c.execute('SELECT value FROM ctown WHERE name = ' + act_name).fetchall()
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

def save_last_results():
    """ To run a year simulation in a week-by-week basis, we need to save the n-week results, so that n+1-week can use
    this state to initialize the simulation
    """
    column_list = tank_list.copy()
    column_list.extend(pump_list)
    column_list.extend(valve_list)

    values = []
    for tank in tank_list:
        values.append(wn.get_node(tank).level)

    for pump in pump_list:
        if type(wn.get_link(pump).status) is int:
            values.append(wn.get_link(pump).status)
        else:
            values.append(wn.get_link(pump).status.value)

    for valve in valve_list:
        if type(wn.get_link(valve).status) is int:
            values.append(wn.get_link(valve).status)
        else:
            values.append(wn.get_link(valve).status.value)

    last_values = pd.DataFrame(data=values)
    last_values = last_values.T
    last_values.columns = column_list
    last_values.to_csv('last_values.csv')

# Week index to initialize the simulation
week_index = int(sys.argv[4])

# connection to the database
conn = sqlite3.connect('ctown_db.sqlite')
c = conn.cursor()


# Create the network
inp_file = sys.argv[2]+'_map.inp'
wn = wntr.network.WaterNetworkModel(inp_file)

dummy_condition = controls.ValueCondition(wn.get_node('T1'), 'level', '>=', -1)


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

list_header.extend(["Attack#01", "Attack#02"])

results_list = []
results_list.append(list_header)

# intialize the simulation with the random demand patterns and tank levels
initialize_simulation()

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
    print('Running simulation using PDD')
    sim = wntr.sim.WNTRSimulator(wn, mode='PDD')
elif sys.argv[1] == 'dd':
    print('Running simulation using DD')
    sim = wntr.sim.WNTRSimulator(wn)
else:
    print('Invalid simulation mode, exiting...')
    sys.exit(1)

# We want to simulate only 1 hydraulic timestep each time MiniCPS processes the simulation data
wn.options.time.duration = wn.options.time.hydraulic_timestep
master_time = 0

if WEEKLY:
    days = 7
else:
    days = 10

iteration_limit = (days*24*3600)/(wn.options.time.hydraulic_timestep)
attack = 0

print("Simulation will run for " + str(days) + " hydraulic timestep is " + str(wn.options.time.hydraulic_timestep) +
      " for a total of " + str(iteration_limit) + " iterations ")

while master_time <= iteration_limit:

    update_controls()
    print("ITERATION %d ------------- " % master_time)
    results = sim.run_sim(convergence_error=True)
    values_list = register_results(results)

    results_list.append(values_list)
    master_time += 1

    for tank in tank_list:
        tank_name = '\'' + tank + '\''
        a_level = wn.get_node(tank).level
        query = "UPDATE ctown SET value = " + str(a_level) + " WHERE name = " + tank_name
        c.execute(query)  # UPDATE TANKS IN THE DATABASE
        conn.commit()

write_results(results_list)