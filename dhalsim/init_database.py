import argparse
import os
import sqlite3
from pathlib import Path

import yaml


class DatabaseInitializer:
    def __init__(self, intermediate_yaml: Path):
        self.intermediate_yaml = intermediate_yaml
        with intermediate_yaml.open(mode='r') as file:
            self.data = yaml.safe_load(file)
        self.db_path = self.data["db_path"]
        self.db_name = self.data["db_name"]

    def write(self):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("""CREATE TABLE """ + self.db_name + """
                (
                    name  TEXT    NOT NULL,
                    pid   INTEGER NOT NULL,
                    value TEXT,
                    PRIMARY KEY (name, pid)
                );""")
            for valve in self.data["valves"]:
                initial_state = "0" if valve["initial_state"].lower() == "closed" else "1"
                cur.execute("INSERT INTO " + self.db_name + " VALUES (?, 1, ?);",
                            (valve["name"], initial_state,))
            for tank in self.data["tanks"]:
                cur.execute("INSERT INTO " + self.db_name + " VALUES (?, 1, ?);",
                            (tank["name"], str(tank["initial_value"], )))
            for pump in self.data["pumps"]:
                initial_state = "0" if pump["initial_state"].lower() == "closed" else "1"
                cur.execute("INSERT INTO " + self.db_name + " VALUES (?, 1, ?);",
                            (pump["name"], initial_state,))
            conn.commit()

    # def write(self):
    #     SCHEMA = """
    #     CREATE TABLE wadi (
    #         name              TEXT NOT NULL,
    #         pid               INTEGER NOT NULL,
    #         value             TEXT,
    #         PRIMARY KEY (name, pid)
    #     );
    #     """
    #
    #     SCHEMA_INIT = """
    #         INSERT INTO wadi VALUES ('T0', 1, '0.5629288');
    #         INSERT INTO wadi VALUES ('T1', 1, '0.3212883');
    #         INSERT INTO wadi VALUES ('T2', 1, '0.1466138');
    #         INSERT INTO wadi VALUES ('P_RAW1', 1, '0');
    #         INSERT INTO wadi VALUES ('P_RAW2', 1, '0');
    #         INSERT INTO wadi VALUES ('V_PUB', 1, '0');
    #         INSERT INTO wadi VALUES ('V_ER1i', 1,'1');
    #         INSERT INTO wadi VALUES ('V_ER1o', 1, '0');
    #         INSERT INTO wadi VALUES ('V_ER2i', 1, '0');
    #         INSERT INTO wadi VALUES ('V_ER2o', 1, '1' );
    #         INSERT INTO wadi VALUES ('P_B1', 1, '1');
    #         INSERT INTO wadi VALUES ('P_B2', 1, '0');
    #         INSERT INTO wadi VALUES ('V_Gi_G', 1,'0');
    #         INSERT INTO wadi VALUES ('V_Gi_B', 1, '1');
    #         INSERT INTO wadi VALUES ('V_SWaT', 1, '0');
    #         INSERT INTO wadi VALUES ('FCV_ER', 1, '1');
    #         INSERT INTO wadi VALUES ('FCV_RWin', 1, '1');
    #         INSERT INTO wadi VALUES ('V1', 1, '1');
    #         INSERT INTO wadi VALUES ('V2', 1, '1');
    #         INSERT INTO wadi VALUES ('V3', 1, '1');
    #         INSERT INTO wadi VALUES ('V4', 1, '1');
    #         INSERT INTO wadi VALUES ('V5', 1, '1');
    #         INSERT INTO wadi VALUES ('V6', 1, '1');
    #         INSERT INTO wadi VALUES ('V7', 1, '1');
    #         INSERT INTO wadi VALUES ('V8', 1, '1');
    #         INSERT INTO wadi VALUES ('V9', 1, '1');
    #         INSERT INTO wadi VALUES ('V10', 1, '1');
    #         INSERT INTO wadi VALUES ('V11', 1, '1');
    #         INSERT INTO wadi VALUES ('V12', 1, '1');
    #         INSERT INTO wadi VALUES ('ATT_1', 1, '0' );
    #         INSERT INTO wadi VALUES ('ATT_2', 1, '0' );
    #     """
    #
    #     with sqlite3.connect(self.db_path) as conn:
    #         cur = conn.cursor()
    #         cur.execute(SCHEMA)
    #         cur.executescript(SCHEMA_INIT)
    #         conn.commit()

    def drop(self):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("DROP TABLE IF EXISTS " + self.db_name + ";")
            conn.commit()

    def print(self):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM " + self.db_name + ";")
            print(cur.fetchall())


def is_valid_file(parser, arg):
    if not os.path.exists(arg):
        parser.error(arg + " does not exist")
    else:
        return arg


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Setup a sqlite DB from a intermediate yaml file')
    parser.add_argument(dest="intermediate_yaml",
                        help="intermediate yaml file", metavar="FILE",
                        type=lambda x: is_valid_file(parser, x))

    args = parser.parse_args()
    db_initializer = DatabaseInitializer(Path(args.intermediate_yaml))

    db_initializer.drop()
    db_initializer.write()
    db_initializer.print()
