X_Pump_1 = ('X_Pump_1', 1)
X_Pump_2 = ('X_Pump_2', 1)
X_Pump_3 = ('X_Pump_3', 1)
X_Pump_4 = ('X_Pump_4', 1)
X_Pump_5 = ('X_Pump_5', 1)
T_1 = ('T_1', 1)
T_2 = ('T_2', 1)
T_3 = ('T_3', 1)
CONTROL = ('CONTROL', 1)

plc_netmask = '/24'
ENIP_LISTEN_PLC_ADDR = '192.168.1.1'
SCADA_IP_ADDR = '192.168.1.2'

CTOWN_IPS = {
    'plc1':'10.0.1.1',
    'plc2':'10.0.2.1',
    'plc3':'10.0.3.1',
}

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


PLC1_TAGS = (
    ('X_Pump_2', 1, 'REAL'),
    ('CONTROL', 1, 'REAL'),
)

PLC2_TAGS = (
    ('X_Pump_4', 1, 'REAL'),
    ('CONTROL', 1, 'REAL'),
)

PLC3_TAGS = (
    ('T_2', 1, 'REAL'),
    ('CONTROL', 1, 'REAL'),
)

SCADA_TAGS = (
    ('X_Pump_1', 1, 'REAL'),
    ('X_Pump_2', 1, 'REAL'),
    ('X_Pump_3', 1, 'REAL'),
    ('X_Pump_4', 1, 'REAL'),
    ('X_Pump_5', 1, 'REAL'),
    ('T_1', 1, 'REAL'),
    ('T_2', 1, 'REAL'),
    ('T_3', 1, 'REAL'),
)

flag_attack_communication_plc1_plc2_replay_empty = 0
flag_attack_plc1 = 0
flag_attack_communication_plc1_plc2 = 0
ATT_1 = ('ATT_1', 1)
ATT_2 = ('ATT_2', 1)

PLC1_SERVER = {
    'address': ENIP_LISTEN_PLC_ADDR,
    'tags': PLC1_TAGS
}
PLC2_SERVER = {
    'address': ENIP_LISTEN_PLC_ADDR,
    'tags': PLC2_TAGS
}
PLC3_SERVER = {
    'address': ENIP_LISTEN_PLC_ADDR,
    'tags': PLC3_TAGS
}

SCADA_SERVER = {
    'address': SCADA_IP_ADDR,
    'tags': SCADA_TAGS
}

PLC1_PROTOCOL = {
    'name': 'enip',
    'mode': 1,
    'server': PLC1_SERVER
}
PLC2_PROTOCOL = {
    'name': 'enip',
    'mode': 1,
    'server': PLC2_SERVER
}
PLC3_PROTOCOL = {
    'name': 'enip',
    'mode': 1,
    'server': PLC3_SERVER
}

SCADA_PROTOCOL = {
    'name': 'enip',
    'mode': 1,
    'server': SCADA_SERVER
}

PATH = 'plant.sqlite'
NAME = 'plant'

STATE = {
    'name': NAME,
    'path': PATH
}

SCHEMA = """        
CREATE TABLE plant (        
    name              TEXT NOT NULL,        
    pid               INTEGER NOT NULL,        
    value             TEXT,        
    PRIMARY KEY (name, pid)        
);
"""

SCHEMA_INIT = """
    INSERT INTO plant VALUES ('T_1', 1, '45.92799552');
    INSERT INTO plant VALUES ('T_2', 1, '46.40400168');
    INSERT INTO plant VALUES ('T_3', 1, '31.73598936');
    INSERT INTO plant VALUES ('X_Pump_1', 1, '0');
    INSERT INTO plant VALUES ('X_Pump_2', 1, '0');
    INSERT INTO plant VALUES ('X_Pump_3', 1, '0');
    INSERT INTO plant VALUES ('X_Pump_4', 1, '0');
    INSERT INTO plant VALUES ('X_Pump_5', 1, '0');
    INSERT INTO plant VALUES ('ATT_1', 1, '0');
    INSERT INTO plant VALUES ('ATT_2', 1, '0');
    INSERT INTO plant VALUES ('CONTROL', 1, '0');
"""