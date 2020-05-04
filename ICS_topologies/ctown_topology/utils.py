"""
sqlite and enip use name (string) and pid (int) has key and the state stores
values as strings.

Actuator tags are redundant, we will use only the XXX_XXX_OPEN tag ignoring
the XXX_XXX_CLOSE with the following convention:
    - 0 = error
    - 1 = off
    - 2 = on

sqlite uses float keyword and cpppo use REAL keyword.
"""

from minicps.utils import build_debug_logger

ctown_log = build_debug_logger(
    name=__name__,
    bytes_per_file=10000,
    rotating_files=2,
    lformat='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    ldir='logs/',
    suffix='')

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
flag_attack_communication_plc1_plc2 = 0
flag_attack_dos_plc2 = 0

################################ Network Configuration ################################################################

# topo {{{1
IP = {
    'plc1': '192.168.1.10',
    'plc2': '192.168.1.20',
    'plc3': '192.168.1.30',
    'plc4': '192.168.1.40',
    'plc5': '192.168.1.50',
    'plc6': '192.168.1.60',
    'plc7': '192.168.1.70',
    'plc8': '192.168.1.80',
    'plc9': '192.168.1.90',
    'scada': '192.168.2.100',
    'attacker': '192.168.1.77',
    'attacker2': '192.168.2.77',
}

NETMASK = '/24'

PLC1_ADDR = IP['plc1']
PLC2_ADDR = IP['plc2']
PLC3_ADDR = IP['plc3']
PLC4_ADDR = IP['plc4']
PLC5_ADDR = IP['plc5']
PLC6_ADDR = IP['plc6']
PLC7_ADDR = IP['plc7']
PLC8_ADDR = IP['plc8']
PLC9_ADDR = IP['plc9']
SCADA_ADDR = IP['scada']

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
    ('T1', 1, 'REAL'),
    ('ATT_1', 1, 'REAL'),
    ('ATT_2', 1, 'REAL')
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
    'address': PLC3_ADDR,
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
    'address': PLC4_ADDR,
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
    'address': PLC5_ADDR,
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
    'address': PLC6_ADDR,
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
    'address': PLC7_ADDR,
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
    'address': PLC9_ADDR,
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
    'address': SCADA_ADDR,
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