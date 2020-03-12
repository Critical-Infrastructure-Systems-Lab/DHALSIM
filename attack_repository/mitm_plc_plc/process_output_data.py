import cip
from scapy.all import *
import pandas as pd
from decimal import Decimal
import time

def process_data(network_data, physical_data):
    data = []
    for i in range(1, 10):
        current_epoch = (datetime.strptime(physical_data.get('timestamps')[i], "%Y-%m-%d %H:%M:%S.%f") - datetime(1970, 1,1)).total_seconds()
        previous_epoch = (datetime.strptime(physical_data.get('timestamps')[i - 1], "%Y-%m-%d %H:%M:%S.%f") - datetime(1970,1,1)).total_seconds()
        for nwk in network_data:
            if (Decimal(nwk.time) + 28800) >= previous_epoch and (Decimal(nwk.time) + 28800) <= current_epoch:
                data_frag = {}
                data_frag['network_data'] = nwk
                data_frag['T_LVL'] = physical_data.get('TANK_LEVEL')[i]
                data_frag['RESERVOIR_LEVEL'] = physical_data.get('RESERVOIR_LEVEL')[i]
                data_frag['J421'] = physical_data.get('J421')[i]
                data_frag['J332'] = physical_data.get('J332')[i]
                data_frag['J156'] = physical_data.get('J156')[i]
                data_frag['J39'] = physical_data.get('J39')[i]
                data_frag['J269'] = physical_data.get('J269')[i]
                data_frag['J273'] = physical_data.get('J273')[i]
                data_frag['J280'] = physical_data.get('J280')[i]
                data_frag['J285'] = physical_data.get('J285')[i]
                data_frag['FLOW_PUMP1'] = physical_data.get('FLOW_PUMP1')[i]
                data_frag['FLOW_PUMP2'] = physical_data.get('FLOW_PUMP2')[i]
                data_frag['STATUS_PUMP1'] = physical_data.get('STATUS_PUMP1')[i]
                data_frag['STATUS_PUMP2'] = physical_data.get('STATUS_PUMP2')[i]
                data_frag['Attack#01'] = physical_data.get('Attack#01')[i]
                data_frag['Attack#02'] = physical_data.get('Attack#02')[i]

                data.append(data_frag)
    return data

network_data = rdpcap("../../Jupyter_notebooks/experiment_data/pressure_driven/attack_mitm_plc2/plc2-eth0.pcap")
physical_data = pd.read_csv("../../Jupyter_notebooks/experiment_data/pressure_driven/attack_mitm_plc2/physical_results.csv")
plc2_data = process_data(network_data, physical_data)