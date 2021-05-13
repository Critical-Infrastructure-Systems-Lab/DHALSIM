import argparse
import os.path
import signal
import subprocess
import sys
import time
from pathlib import Path

import yaml

from dhalsim.init_database import DatabaseInitializer


def is_valid_file(parser, arg):
    if not os.path.exists(arg):
        parser.error(arg + " does not exist")
    else:
        return arg


class Runner():
    def __init__(self, config_file, output_folder):
        self.config_file = config_file
        self.output_folder = output_folder

        signal.signal(signal.SIGINT, self.sigint_handler)
        signal.signal(signal.SIGTERM, self.sigint_handler)

        self.intermediate_yaml_path = Path(
            __file__).parent.parent.absolute() / "examples" / "wadi_topology" / "intermediate.yaml"

        self.automatic_run = None

    def sigint_handler(self, sig, frame):
        os.kill(self.automatic_run.pid, signal.SIGTERM)
        sys.exit(0)

    def run(self):
        db_initializer = DatabaseInitializer(self.intermediate_yaml_path)

        db_initializer.drop()
        db_initializer.write()
        db_initializer.print()

        automatic_run_path = Path(__file__).parent.absolute() / "python2" / "automatic_run.py"
        self.automatic_run = subprocess.Popen(
            ["python2", str(automatic_run_path), str(self.intermediate_yaml_path)])
        self.automatic_run.wait()


def main():
    parser = argparse.ArgumentParser(description='Do the DHALSIM')  # Todo Change description
    parser.add_argument(dest="config_file",
                        help="config file", metavar="FILE",
                        type=lambda x: is_valid_file(parser, x))
    parser.add_argument('-o', '--output', dest='output_folder', metavar="FOLDER",
                        help='folder to put the output files', type=str)

    args = parser.parse_args()

    config_file = Path(args.config_file)
    output_folder = Path(args.output_folder if args.output_folder else "output")

    runner = Runner(config_file, output_folder)
    runner.run()

if __name__ == '__main__':
    main()
