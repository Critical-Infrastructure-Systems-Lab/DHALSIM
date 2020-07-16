from minicps.states import SQLiteState
from utils import PATH, SCHEMA, SCHEMA_INIT
from sqlite3 import OperationalError

"""
This script generates the sqlite used to store the system state while the simulation is running
"""

if __name__ == "__main__":

    try:
        SQLiteState._create(PATH, SCHEMA)
        SQLiteState._init(PATH, SCHEMA_INIT)
        print "{} successfully created.".format(PATH)
    except OperationalError:
        print "{} already exists.".format(PATH)