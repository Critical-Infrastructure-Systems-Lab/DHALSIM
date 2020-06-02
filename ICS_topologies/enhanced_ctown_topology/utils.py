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
flag_attack_communication_plc1_plc2 = 1
flag_attack_dos_plc2 = 0

################################ Network Configuration ################################################################

# topo {{{1
IP = {
    'plc_ip': '192.168.1.1',
    'scada': '192.168.1.2',
}

plc_netmask = '/24'

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