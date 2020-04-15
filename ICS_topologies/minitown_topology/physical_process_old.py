import wntr
import wntr.network.controls as controls
import sqlite3
import csv
import time
import sys

# connection to the database
conn = sqlite3.connect('minitown_db.sqlite')
c = conn.cursor()

# Master time used to synchronize the PLCs
rows = c.execute("SELECT value FROM minitown WHERE name = 'TIME'").fetchall()
conn.commit()
master_time = int(rows[0][0])  # PUMP1 STATUS FROM DATABASE

# Create the network
inp_file = sys.argv[2]+'_map.inp'
wn = wntr.network.WaterNetworkModel(inp_file)

# Set option for step-by-step simulation
wn.options.time.duration = 900
wn.options.time.hydraulic_timestep = 900
wn.options.time.pattern_timestep = 3600
linkStatus = wntr.network.base.LinkStatus

results_list = []
list_header = []

node_list = list(wn.node_name_list)
junction_list = []
for node in node_list:
    if wn.get_node(node).node_type == 'Junction':
        junction_list.append(str(node))

list_header = ["iteration", "timestamps", "TANK_LEVEL", "RESERVOIR_LEVEL"]
list_header.extend(junction_list)
another_list = ["FLOW_PUMP1", "FLOW_PUMP2", "STATUS_PUMP1", "STATUS_PUMP2", "Attack#01", "Attack#02"]
list_header.extend(another_list)

results_list.append(list_header)

# SET THE RIGHT DATA IN DB
tank = wn.get_node("TANK")  # WNTR TANK OBJECT
pump1 = wn.get_link("PUMP1")  # WNTR PUMP OBJECT
pump2 = wn.get_link("PUMP2")  # WNTR PUMP OBJECT
reservoir = wn.get_node("R1")

# Since we now use the same inp file, we need to delete the default controls
for control in wn.control_name_list:
    wn.remove_control(control)

# We define a dummy condition that should always be true
condition = controls.ValueCondition(tank, 'level', '>=', -1)

rows = c.execute("SELECT value FROM minitown WHERE name = 'P1_STS'").fetchall()
conn.commit()
pump1_status = rows[0][0]  # PUMP1 STATUS FROM DATABASE
act1 = controls.ControlAction(pump1, 'status', 0)
pump1_control = controls.Control(condition, act1, name='pump1control')

rows = c.execute("SELECT value FROM minitown WHERE name = 'P2_STS'").fetchall()
conn.commit()
pump2_status = rows[0][0]  # PUMP1 STATUS FROM DATABASE
act2 = controls.ControlAction(pump2, 'status', 1)
pump2_control = controls.Control(condition, act2, name='pump2control')

wn.add_control('WnPump1Control', pump1_control)
wn.add_control('WnPump2Control', pump2_control)

if sys.argv[1] == 'pdd':
    print('Running simulation using PDD')
    sim = wntr.sim.WNTRSimulator(wn, mode='PDD')
elif sys.argv[1] == 'dd':
    print('Running simulation using DD')
    sim = wntr.sim.WNTRSimulator(wn)
else:
    print('Invalid simulation mode, exiting...')
    sys.exit(1)

days_simulated = 7
iteration_limit = days_simulated*(24*3600) / wn.options.time.duration

# START STEP BY STEP SIMULATION
while master_time <= iteration_limit:

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

    rows = c.execute("SELECT value FROM minitown WHERE name = 'CONTROL'").fetchall()
    conn.commit()
    control = int(rows[0][0])  # PUMP1 STATUS FROM DATABASE

    if control == 1:
        master_time += 1
        results = sim.run_sim(convergence_error=True)

        print("ITERATION %d ------------- " % master_time)
        print("Tank Level %f " % tank.level)

        c.execute("UPDATE minitown SET value = %f WHERE name = 'T_LVL'" % tank.level)  # UPDATE TANK LEVEL IN THE DATABASE
        conn.commit()

        c.execute("UPDATE minitown SET value = %d WHERE name = 'TIME'" % master_time)  # UPDATE TANK LEVEL IN THE DATABASE
        conn.commit()

        # take the value of attacks labels from the database
        rows = c.execute("SELECT value FROM minitown WHERE name = 'ATT_1'").fetchall()
        conn.commit()
        attack1 = rows[0][0]

        rows = c.execute("SELECT value FROM minitown WHERE name = 'ATT_2'").fetchall()
        conn.commit()
        attack2 = rows[0][0]

        values_list = []

        values_list.extend([master_time, results.timestamp, tank.level, reservoir.head])
        for junction in junction_list:
            values_list.extend([wn.get_node(junction).head - wn.get_node(junction).elevation])

        values_list.extend([pump1.flow, pump2.flow, pump1_status, pump2_status, attack1, attack2])

        results_list.append(values_list)

        c.execute("UPDATE minitown SET value = 0 WHERE name = 'CONTROL'")
        conn.commit()

        if results:
            time.sleep(0.5)

    else:
        continue

with open('output/'+sys.argv[3], 'w', newline='\n') as f:
    writer = csv.writer(f)
    writer.writerows(results_list)