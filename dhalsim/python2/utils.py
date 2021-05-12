"""
utils files define the following:
- The tags stored in the sqlite db and exchanged by the devices using ENIP. These tags represent variables in the system; hence, a "T0" tank represents the level of tank 0
  In addition, two special tags are used: ATT_1 and ATT_2, these are used to signal the presence of an attack
- setting flags that enable the devices if they're being compromised and the attack behavior.
- network configuration: That section configures the ENIP devices in the simulation
- database configuration, while the simulation is running, the system state is stored in a sqlite database
"""

from minicps.utils import build_debug_logger

wadi_log = build_debug_logger(
    name=__name__,
    bytes_per_file=10000,
    rotating_files=2,
    lformat='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    ldir='logs/',
    suffix='')

################################ System State Variables ################################################################

T0 = ('T0', 1)
T1 = ('T1', 1)
T2 = ('T2', 1)

P_RAW1 = ('P_RAW1', 1)
P_RAW2 = ('P_RAW2', 1)

P_B2 = ('P_B2', 1)
P_B1 = ('P_B1', 1)

V_Gi_G = ('V_Gi_G', 1)
V_Gi_B = ('V_Gi_B', 1)
V_SWaT = ('V_SWaT', 1)
V_PUB = ('V_PUB', 1)
V_ER2i = ('V_ER2i', 1)
V_ER2o = ('V_ER2o', 1)
V_ER1i = ('V_ER1i', 1)
V_ER1o = ('V_ER1o', 1)
FCV_ER = ('FCV_ER', 1)
FCV_RWin = ('FCV_RWin', 1)
V1 = ('V1', 1)
V2 = ('V2', 1)
V3 = ('V3', 1)
V4 = ('V4', 1)
V5 = ('V5', 1)
V6 = ('V6', 1)
V7 = ('V7', 1)
V8 = ('V8', 1)
V9 = ('V9', 1)
V10 = ('V10', 1)
V11 = ('V11', 1)
V12 = ('V12', 1)

################################ Attack Flags ################################################################
ATT_1 = ('ATT_1', 1)
ATT_2 = ('ATT_2', 1)

flag_attack_plc1 = 0
flag_attack_plc2 = 0
flag_attack_communication_plc1_scada = 0
flag_attack_communication_plc1_plc2 = 0
flag_attack_dos_plc2 = 0

################################ Network Configuration ################################################################

# topo {{{1
wadi_ip = {
    'plc1': '192.168.1.10',
    'plc2': '192.168.1.20',
    'plc3': '192.168.1.30',
    'scada': '192.168.2.30',
    'attacker': '192.168.1.77',
    'attacker2': '192.168.2.77',
}

NETMASK = '/24'

MAC = {
    'plc1': '00:1D:9C:C7:B0:70',
    'plc2': '00:1D:9C:C8:BC:46',
    'plc3': '00:1D:9C:C8:BC:57',
    'scada': '64:00:6A:70:86:D0',
    'attacker': 'AA:AA:AA:AA:AA:AA',
    'attacker2': 'BB:BB:BB:BB:BB:BB',
}

PLC1_ADDR = wadi_ip['plc1']
PLC2_ADDR = wadi_ip['plc2']
PLC3_ADDR = wadi_ip['plc2']
SCADA_ADDR = wadi_ip['scada']

PLC1_DATA = {
    'TODO': 'TODO',
}

PLC2_DATA = {
    'TODO': 'TODO',
}

PLC3_DATA = {
    'TODO': 'TODO',
}

SCADA_DATA = {
    'TODO': 'TODO',
}

# Adding plc1------------------------------------------------
PLC1_TAGS = (
    ('T0', 1, 'REAL'),
    ('T2', 1, 'REAL'),
    ('P_RAW1', 1, 'REAL'),
    ('V_PUB', 1, 'REAL'),
    ('ATT_1', 1, 'REAL'),
    ('ATT_2', 1, 'REAL')
)

PLC1_SERVER = {
    'address': PLC1_ADDR,
    'tags': PLC1_TAGS
}
PLC1_PROTOCOL = {
    'name': 'enip',
    'mode': 1,
    'server': PLC1_SERVER
}

# Adding plc2-------------------------------------------
PLC2_TAGS = (
    ('ATT_1', 1, 'REAL'),
    ('ATT_2', 1, 'REAL'),
    ('T2', 1, 'REAL'),
    ('V_ER2i', 1, 'REAL')
)

PLC2_SERVER = {
    'address': PLC2_ADDR,
    'tags': PLC2_TAGS
}
PLC2_PROTOCOL = {
    'name': 'enip',
    'mode': 1,
    'server': PLC2_SERVER
}

# Adding scada--------------------------------------------
SCADA_TAGS = (
    ('T0', 1, 'REAL'),
    ('T1', 1, 'REAL'),
    ('T2', 1, 'REAL'),
    ('P_RAW1', 1, 'REAL'),
    ('P_RAW2', 1, 'REAL'),
    ('V_PUB', 1, 'REAL'),
    ('V_ER1i', 1, 'REAL'),
    ('V_ER1o', 1, 'REAL'),
    ('V_ER2i', 1, 'REAL'),
    ('V_ER2o', 1, 'REAL'),
    ('P_B1', 1, 'REAL'),
    ('P_B2', 1, 'REAL'),
    ('V_Gi_G', 1, 'REAL'),
    ('V_Gi_B', 1, 'REAL'),
    ('V_SWaT', 1, 'REAL'),
    ('FCV_ER', 1, 'REAL'),
    ('FCV_RWin', 1, 'REAL'),
    ('ATT_1', 1, 'REAL'),
    ('ATT_2', 1, 'REAL')
)

SCADA_SERVER = {
    'address': SCADA_ADDR,
    'tags': SCADA_TAGS
}

SCADA_PROTOCOL = {
    'name': 'enip',
    'mode': 1,
    'server': SCADA_SERVER
}

# Adding Attacker-----------------------------------------
ATT_ADDR = wadi_ip['attacker']

ATT_TAGS = (
    ('T0', 1, 'REAL'),
    ('P1_STS', 1, 'REAL'),
    ('P2_STS', 1, 'REAL'),
    ('ATT_1', 1, 'REAL'),
    ('ATT_2', 1, 'REAL')
)

ATT_SERVER = {
    'address': ATT_ADDR,
    'tags': ATT_TAGS
}

ATT_PROTOCOL = {
    'name': 'enip',
    'mode': 1,
    'server': ATT_SERVER
}

# Adding Attacker_SCADA-----------------------------------------

ATT2_ADDR = wadi_ip['attacker2']

ATT2_TAGS = (
    ('T0', 1, 'REAL'),
    ('P1_STS', 1, 'REAL'),
    ('P2_STS', 1, 'REAL'),
    ('ATT_1', 1, 'REAL'),
    ('ATT_2', 1, 'REAL')
)

ATT2_SERVER = {
    'address': ATT2_ADDR,
    'tags': ATT2_TAGS
}

ATT2_PROTOCOL = {
    'name': 'enip',
    'mode': 1,
    'server': ATT2_SERVER
}

# ---------------------------------------------------------
# SPHINX_SWAT_TUTORIAL STATE(
PATH = '/home/luc/dhalsim.sqlite'
NAME = 'wadi'

STATE = {
    'name': NAME,
    'path': PATH
}
# SPHINX_SWAT_TUTORIAL STATE)

SCHEMA = """
CREATE TABLE wadi (
    name              TEXT NOT NULL,
    pid               INTEGER NOT NULL,
    value             TEXT,
    PRIMARY KEY (name, pid)
);
"""

SCHEMA_INIT = """
    INSERT INTO wadi VALUES ('T0', 1, '0.5629288');
    INSERT INTO wadi VALUES ('T1', 1, '0.3212883');
    INSERT INTO wadi VALUES ('T2', 1, '0.1466138');
    INSERT INTO wadi VALUES ('P_RAW1', 1, '0');
    INSERT INTO wadi VALUES ('P_RAW2', 1, '0');  
    INSERT INTO wadi VALUES ('V_PUB', 1, '0');  
    INSERT INTO wadi VALUES ('V_ER1i', 1,'1');  
    INSERT INTO wadi VALUES ('V_ER1o', 1, '0');  
    INSERT INTO wadi VALUES ('V_ER2i', 1, '0'); 
    INSERT INTO wadi VALUES ('V_ER2o', 1, '1' );       
    INSERT INTO wadi VALUES ('P_B1', 1, '1');  
    INSERT INTO wadi VALUES ('P_B2', 1, '0');  
    INSERT INTO wadi VALUES ('V_Gi_G', 1,'0');
    INSERT INTO wadi VALUES ('V_Gi_B', 1, '1');  
    INSERT INTO wadi VALUES ('V_SWaT', 1, '0');    
    INSERT INTO wadi VALUES ('FCV_ER', 1, '1');  
    INSERT INTO wadi VALUES ('FCV_RWin', 1, '1');    
    INSERT INTO wadi VALUES ('V1', 1, '1');
    INSERT INTO wadi VALUES ('V2', 1, '1');
    INSERT INTO wadi VALUES ('V3', 1, '1');
    INSERT INTO wadi VALUES ('V4', 1, '1');
    INSERT INTO wadi VALUES ('V5', 1, '1');
    INSERT INTO wadi VALUES ('V6', 1, '1');
    INSERT INTO wadi VALUES ('V7', 1, '1');
    INSERT INTO wadi VALUES ('V8', 1, '1');
    INSERT INTO wadi VALUES ('V9', 1, '1');
    INSERT INTO wadi VALUES ('V10', 1, '1');
    INSERT INTO wadi VALUES ('V11', 1, '1');
    INSERT INTO wadi VALUES ('V12', 1, '1');
    INSERT INTO wadi VALUES ('ATT_1', 1, '0' );  
    INSERT INTO wadi VALUES ('ATT_2', 1, '0' );            
"""
