import subprocess
import time
import sys
import argparse
import signal
import yaml

class NodeControl():

    """
    This class represents a PLC or SCADA node. All of these devices have the same pattern of launching a tcpdump process
    in the eth0 interface, launching a plc_n.py script or scada.py script and when receives a SIGINT or SIGTERM signal
    store the recevied values into a .csv file. In addition, a pcap file is created with the tcpdump results
    """

    def sigint_handler(self, sig, frame):
        self.terminate()
        sys.exit(0)

    def terminate(self):
        """
        All the subprocesses launched in this Digital Twin follow the same pattern to ensure that they finish before
        continuing with the finishing of the parent process
        """
        print("Stopping Tcp dump process on PLC...")
        self.process_tcp_dump.kill()

        print("Stopping PLC...")
        self.plc_process.send_signal(signal.SIGINT)
        self.plc_process.wait()
        if self.plc_process.poll() is None:
            self.plc_process.terminate()
        if self.plc_process.poll() is None:
            self.plc_process.kill()

    def get_plc_dict(self, plc_list):
        for plc in plc_list:
            if plc['PLC'] == self.name:
                return plc

    def main(self):
        """
        Main method of a device. The signal handler methods are define, the routing is configured (adding default
        gateways for the deviceS), a tcpdump process is started
        and a plc_n.py or scada.py script is launched
        :return:
        """
        args = self.get_arguments()
        self.process_arguments(args)

        signal.signal(signal.SIGINT, self.sigint_handler)
        signal.signal(signal.SIGTERM, self.sigint_handler)

        with open(self.config_path, 'r') as config_file:
            config_data = yaml.full_load(config_file)
            if 'initial_custom_flag' in config_data:
                if 'week_index' in config_data:
                    self.week_index = config_data['week_index']
                else:
                    self.week_index = 0

        self.interface_name = self.name.lower() + '-eth0'
        self.delete_log()

        self.process_tcp_dump = self.start_tcpdump_capture()
        self.plc_process = self.start_plc()

        while self.plc_process.poll() is None:
            pass

        self.terminate()

    def delete_log(self):
        """
        We delete the log of previous experiments
        :return:
        """
        subprocess.call(['rm', '-rf', self.name + '.log'])

    def start_tcpdump_capture(self):
        pcap = self.interface_name+'.pcap'
        tcp_dump = subprocess.Popen(['tcpdump', '-i', self.interface_name, '-w', 'output/'+pcap], shell=False)
        return tcp_dump

    def start_plc(self):
        plc_process = subprocess.Popen(['python', 'plc.py', '-n', self.name, '-w', str(self.week_index), '-d', self.dict_path, '-l', self.last], shell=False)
        return plc_process

    def process_arguments(self, arg_parser):
        if arg_parser.config:
            self.config_path = arg_parser.config
        else:
            self.config_path = "c_town_config.yaml"

        if arg_parser.name:
            self.name = arg_parser.name
        else:
            self.name = "PLC1"

        if arg_parser.dict:
            self.dict_path = arg_parser.dict
        else:
            self.dict_path = "data"

        if arg_parser.last:
            self.last = arg_parser.last
        else:
            self.last = 0

    def get_arguments(self):
        parser = argparse.ArgumentParser(description='Master Script of a node in Minicps')
        parser.add_argument("--config", "-c", help="Path of the experiment config file")
        parser.add_argument("--name", "-n", help="Name of the PLC or SCADA to run")
        parser.add_argument("--dict", "-d", help="Path of the PLCs dict file")
        parser.add_argument("--last", "-l", help="Flag that indicates that this is the last PLC in the experiment. "
                                                 "Acepted values are 1 or 0")
        return parser.parse_args()


if __name__ == " __main__":
    node_control = NodeControl()
    node_control.main()