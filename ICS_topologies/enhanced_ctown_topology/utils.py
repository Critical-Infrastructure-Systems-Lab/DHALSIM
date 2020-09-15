"""
utils files define the following:
- The tags stored in the sqlite db and exchanged by the devices using ENIP. These tags represent variables in the system; hence, a "T0" tank represents the level of tank 0
  In addition, two special tags are used: ATT_1 and ATT_2, these are used to signal the presence of an attack
- setting flags that enable the devices if they're being compromised and the attack behavior.
- network configuration: That section configures the ENIP devices in the simulation
- database configuration, while the simulation is running, the system state is stored in a sqlite database
"""
################################ System State Variables ################################################################
T1 = ('T1', 1)
T2 = ('T2', 1)
T3 = ('T3', 1)
T4 = ('T4', 1)
T5 = ('T5', 1)
T6 = ('T6', 1)
T7 = ('T7', 1)

################################ Actuators ################################################################
PU1 = ('PU1', 1)
PU2 = ('PU2', 1)
PU3 = ('PU3', 1)
PU4 = ('PU4', 1)
PU5 = ('PU5', 1)
PU6 = ('PU6', 1)
PU7 = ('PU7', 1)
PU8 = ('PU8', 1)
PU9 = ('PU9', 1)
PU10 = ('PU10', 1)
PU11 = ('PU11', 1)

v1 = ('v1', 1)
V2 = ('V2', 1)


################################ Attack Flags ################################################################
ATT_1 = ('ATT_1', 1)
ATT_2 = ('ATT_2', 1)

flag_attack_plc1 = 0
flag_attack_plc2 = 0
flag_attack_communication_plc1_scada = 0
flag_attack_communication_plc1_plc2 = 1
flag_attack_dos_plc2 = 0

################################ Network Configuration ################################################################

plc_netmask = '/24'
ENIP_LISTEN_PLC_ADDR = '192.168.1.1'
SCADA_IP_ADDR = '192.168.1.2'

CTOWN_IPS = {
    'plc1':'10.0.1.1',
    'plc2':'10.0.2.1',
    'plc3':'10.0.3.1',
    'plc4':'10.0.4.1',
    'plc5':'10.0.5.1',
    'plc6':'10.0.6.1',
    'plc7':'10.0.7.1',
    'plc8':'10.0.8.1',
    'plc9':'10.0.9.1',
}

############################## ENIP Servers Configuration ##############################

PLC1_DATA = {
    'TODO': 'TODO',
}

PLC2_DATA = {
    'TODO': 'TODO',
}

PLC3_DATA = {
    'TODO': 'TODO',
}

PLC4_DATA = {
    'TODO': 'TODO',
}

PLC5_DATA = {
    'TODO': 'TODO',
}
PLC6_DATA = {
    'TODO': 'TODO',
}
PLC7_DATA = {
    'TODO': 'TODO',
}
PLC8_DATA = {
    'TODO': 'TODO',
}
PLC9_DATA = {
    'TODO': 'TODO',
}

SCADA_DATA = {
    'TODO': 'TODO',
}

# Adding plc1------------------------------------------------
PLC1_TAGS = (
    ('T1', 1, 'REAL'),
    ('PU1', 1, 'REAL'),
    ('PU2', 1, 'REAL'),
    ('ATT_1', 1, 'REAL'),
    ('ATT_2', 1, 'REAL')
)
PLC1_SERVER = {
    'address': ENIP_LISTEN_PLC_ADDR,
    'tags': PLC1_TAGS
}
PLC1_PROTOCOL = {
    'name': 'enip',
    'mode': 1,
    'server': PLC1_SERVER
}

# Adding plc2-------------------------------------------
PLC2_TAGS = (
    ('T1', 1, 'REAL'),
    ('ATT_1', 1, 'REAL'),
    ('ATT_2', 1, 'REAL')
)
PLC2_SERVER = {
    'address': ENIP_LISTEN_PLC_ADDR,
    'tags': PLC2_TAGS
}
PLC2_PROTOCOL = {
    'name': 'enip',
    'mode': 1,
    'server': PLC2_SERVER
}

PLC3_TAGS = (
    ('T2', 1, 'REAL'),
    ('V2', 1, 'REAL'),
    ('T3', 1, 'REAL'),
    ('PU4', 1, 'REAL'),
    ('PU5', 1, 'REAL'),
    ('PU6', 1, 'REAL'),
    ('PU7', 1, 'REAL'),
    ('ATT_1', 1, 'REAL'),
    ('ATT_2', 1, 'REAL')
)
PLC3_SERVER = {
    'address': ENIP_LISTEN_PLC_ADDR,
    'tags': PLC3_TAGS
}
PLC3_PROTOCOL = {
    'name': 'enip',
    'mode': 1,
    'server': PLC3_SERVER
}

PLC4_TAGS = (
    ('T3', 1, 'REAL'),
    ('ATT_1', 1, 'REAL'),
    ('ATT_2', 1, 'REAL')
)
PLC4_SERVER = {
    'address': ENIP_LISTEN_PLC_ADDR,
    'tags': PLC4_TAGS
}
PLC4_PROTOCOL = {
    'name': 'enip',
    'mode': 1,
    'server': PLC4_SERVER
}

PLC5_TAGS = (
    ('T5', 1, 'REAL'),
    ('T7', 1, 'REAL'),
    ('PU8', 1, 'REAL'),
    ('PU10', 1, 'REAL'),
    ('PU11', 1, 'REAL'),
    ('ATT_1', 1, 'REAL'),
    ('ATT_2', 1, 'REAL')
)
PLC5_SERVER = {
    'address': ENIP_LISTEN_PLC_ADDR,
    'tags': PLC5_TAGS
}
PLC5_PROTOCOL = {
    'name': 'enip',
    'mode': 1,
    'server': PLC5_SERVER
}

PLC6_TAGS = (
    ('T4', 1, 'REAL'),
    ('ATT_1', 1, 'REAL'),
    ('ATT_2', 1, 'REAL')
)
PLC6_SERVER = {
    'address': ENIP_LISTEN_PLC_ADDR,
    'tags': PLC6_TAGS
}
PLC6_PROTOCOL = {
    'name': 'enip',
    'mode': 1,
    'server': PLC6_SERVER
}

PLC7_TAGS = (
    ('T5', 1, 'REAL'),
    ('ATT_1', 1, 'REAL'),
    ('ATT_2', 1, 'REAL')
)
PLC7_SERVER = {
    'address': ENIP_LISTEN_PLC_ADDR,
    'tags': PLC7_TAGS
}
PLC7_PROTOCOL = {
    'name': 'enip',
    'mode': 1,
    'server': PLC7_SERVER
}


PLC9_TAGS = (
    ('T7', 1, 'REAL'),
    ('ATT_1', 1, 'REAL'),
    ('ATT_2', 1, 'REAL')
)
PLC9_SERVER = {
    'address': ENIP_LISTEN_PLC_ADDR,
    'tags': PLC9_TAGS
}
PLC9_PROTOCOL = {
    'name': 'enip',
    'mode': 1,
    'server': PLC9_SERVER
}


# Adding scada--------------------------------------------
SCADA_TAGS = (
    ('T1', 1, 'REAL'),
    ('T2', 1, 'REAL'),
    ('T3', 1, 'REAL'),
    ('T4', 1, 'REAL'),
    ('T5', 1, 'REAL'),
    ('T7', 1, 'REAL'),
    ('PU1', 1, 'REAL'),
    ('PU2', 1, 'REAL'),
    ('PU4', 1, 'REAL'),
    ('PU5', 1, 'REAL'),
    ('PU6', 1, 'REAL'),
    ('PU7', 1, 'REAL'),
    ('PU8', 1, 'REAL'),
    ('PU10', 1, 'REAL'),
    ('PU11', 1, 'REAL'),
    ('V2', 1, 'REAL'),
    ('ATT_1', 1, 'REAL'),
    ('ATT_2', 1, 'REAL')
)

SCADA_SERVER = {
    'address': SCADA_IP_ADDR,
    'tags': SCADA_TAGS
}

SCADA_PROTOCOL = {
    'name': 'enip',
    'mode': 1,
    'server': SCADA_SERVER
}



# ---------------------------------------------------------
# SPHINX_SWAT_TUTORIAL STATE(
PATH = 'ctown_db.sqlite'
NAME = 'ctown'

STATE = {
    'name': NAME,
    'path': PATH
}
# SPHINX_SWAT_TUTORIAL STATE)

SCHEMA = """
CREATE TABLE ctown (
    name              TEXT NOT NULL,
    pid               INTEGER NOT NULL,
    value             TEXT,
    PRIMARY KEY (name, pid)
);
"""

SCHEMA_INIT = """
    INSERT INTO ctown VALUES ('T1', 1, '3.0');
    INSERT INTO ctown VALUES ('T2', 1, '0.5');
    INSERT INTO ctown VALUES ('T3', 1, '3.0');
    INSERT INTO ctown VALUES ('T4', 1, '2.5');
    INSERT INTO ctown VALUES ('T5', 1, '1.0');  
    INSERT INTO ctown VALUES ('T6', 1, '5.2');
    INSERT INTO ctown VALUES ('T7', 1, '2.5');  
    INSERT INTO ctown VALUES ('PU1', 1,'0');  
    INSERT INTO ctown VALUES ('PU2', 1, '1');  
    INSERT INTO ctown VALUES ('PU3', 1, '0');
    INSERT INTO ctown VALUES ('PU4', 1, '0'); 
    INSERT INTO ctown VALUES ('PU5', 1, '0' );       
    INSERT INTO ctown VALUES ('PU6', 1, '0');  
    INSERT INTO ctown VALUES ('PU7', 1, '0');  
    INSERT INTO ctown VALUES ('PU8', 1,'0');
    INSERT INTO ctown VALUES ('PU9', 1,'0');
    INSERT INTO ctown VALUES ('PU10', 1, '0');  
    INSERT INTO ctown VALUES ('PU11', 1, '0');
    INSERT INTO ctown VALUES ('v1', 1, '1');    
    INSERT INTO ctown VALUES ('V2', 1, '0');
    INSERT INTO ctown VALUES ('V45', 1, '1');    
    INSERT INTO ctown VALUES ('V47', 1, '1');
    INSERT INTO ctown VALUES ('ATT_1', 1, '0' );  
    INSERT INTO ctown VALUES ('ATT_2', 1, '0' );            
"""
