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


master_time = 0

# connection to the database
conn = sqlite3.connect('ctown_db.sqlite')
c = conn.cursor()

# Create the network
inp_file = sys.argv[2]+'_map.inp'
wn = wntr.network.WaterNetworkModel(inp_file)

# All times in seconds
wn.options.time.duration = 1
wn.options.time.hydraulic_timestep = 5*60
wn.options.time.quality_timestep = 5*60
wn.options.time.pattern_timestep = 60*60
wn.options.time.report_timestep = 5*60

list_header = []
node_list = list(wn.node_name_list)
link_list = list(wn.link_name_list)

tank_list = get_node_list_by_type(node_list, 'Tank')
junction_list = get_node_list_by_type(node_list, 'Junction')
pump_list = get_link_list_by_type(link_list, 'Pump')
valve_list = get_link_list_by_type(link_list, 'Valve')


list_header = ["Timestamps"]
aux = create_node_header(tank_list)
list_header.extend(aux)

aux = create_node_header(junction_list)
list_header.extend(aux)

aux = create_link_header(pump_list)
list_header.extend(aux)

aux = create_link_header(valve_list)
list_header.extend(aux)

results_list = [list_header]

# We define a dummy condition that should always be true
condition = controls.ValueCondition(wn.get_node('T1'), 'level', '>=', -1)

# Create an action and control object for each actuator. Add that control object to the wn

if sys.argv[1] == 'pdd':
    print('Running simulation using PDD')
    sim = wntr.sim.WNTRSimulator(wn, mode='PDD')
elif sys.argv[1] == 'dd':
    print('Running simulation using DD')
    sim = wntr.sim.WNTRSimulator(wn)
else:
    print('Invalid simulation mode, exiting...')
    sys.exit(1)

days_simulated = 1
iteration = 0
iteration_limit = days_simulated*(24*3600) / wn.options.time.duration

# START STEP BY STEP SIMULATION
while iteration <= iteration_limit:

    # Get updated values from the database of : -VALVE VALUE -PUMPS VALUES
    #  UPDATE WNTR PUMP1 STATUS FROM DATABASE
    rows_1 = c.execute("SELECT value FROM minitown WHERE name = 'P1_STS'").fetchall()
    conn.commit()

    rows_2 = c.execute("SELECT value FROM minitown WHERE name = 'P2_STS'").fetchall()
    conn.commit()

    pump1_status = rows_1[0][0]  # PUMP1 STATUS FROM DATABASE
    act1 = controls.ControlAction(pump1, 'status', int(pump1_status))
    pump1_control = controls.Control(condition, act1, name='pump1control')

    #  UPDATE WNTR PUMP2 STATUS FROM DATABASE
    pump2_status = rows_2[0][0]  # PUMP1 STATUS FROM DATABASE
    act2 = controls.ControlAction(pump2, 'status', int(pump2_status))
    pump2_control = controls.Control(condition, act2, name='pump2control')

    wn.remove_control("WnPump1Control")
    wn.remove_control("WnPump2Control")

    wn.add_control('WnPump1Control', pump1_control)
    wn.add_control('WnPump2Control', pump2_control)

    results = sim.run_sim(convergence_error=True)

    print ("ITERATION %d ------------------" % iteration)

    c.execute("UPDATE minitown SET value = %f WHERE name = 'T_LVL'" % tank.level)  # UPDATE TANK LEVEL IN THE DATABASE
    conn.commit()

    # take the value of attacks labels from the database
    rows = c.execute("SELECT value FROM minitown WHERE name = 'ATT_1'").fetchall()
    conn.commit()
    attack1 = rows[0][0]

    rows = c.execute("SELECT value FROM minitown WHERE name = 'ATT_2'").fetchall()
    conn.commit()
    attack2 = rows[0][0]

    values_list = []

    values_list.extend([results.timestamp, tank.level, reservoir.head])
    for junction in junction_list:
        values_list.extend([wn.get_node(junction).head - wn.get_node(junction).elevation])

    values_list.extend([pump1.flow, pump2.flow, pump1_status, pump2_status, attack1, attack2])

    results_list.append(values_list)

    iteration += 1

    if results:
        time.sleep(0.5)

with open('output/'+sys.argv[3], 'w', newline='\n') as f:
    writer = csv.writer(f)
    writer.writerows(results_list)
