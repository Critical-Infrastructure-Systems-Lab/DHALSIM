import network

net = network.WaterDistributionNetwork("ctown_pd.inp")
net.set_time_params(duration=3600, hydraulic_step=300)

status = 0.0
if net.valves:
    actuators_update_dict = {uid: status for uid in net.pumps.uid.append(net.valves.uid)}
else:
    actuators_update_dict = {uid: status for uid in net.pumps.uid}

print(actuators_update_dict)
exit(0)

net.run(interactive=False, status_dict=actuators_update_dict)

for pump in net.pumps.uid:
	print(net.df_links_report['pumps', pump, 'status'])