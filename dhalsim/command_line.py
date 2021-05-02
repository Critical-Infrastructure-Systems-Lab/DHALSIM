import argparse
import os.path

import yaml


def is_valid_file(parser, arg):
    if not os.path.exists(arg):
        parser.error(arg + " does not exist")
    else:
        return arg


def main():
    parser = argparse.ArgumentParser(description='Do the DHALSIM') #Todo Change description
    parser.add_argument(dest="config_file",
                        help="config file", metavar="FILE",
                        type=lambda x: is_valid_file(parser, x))
    parser.add_argument('-o', '--output', dest='output_folder', metavar="FOLDER",
                        help='folder to put the output files', type=str)

    args = parser.parse_args()

    config_file = os.path.abspath(args.config_file)
    output_folder =  os.path.abspath(args.output_folder if args.output_folder else "output")

    print(yaml.dump(config_file))

    print(config_file, output_folder)

if __name__ == '__main__':
    main()
