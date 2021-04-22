import subprocess
import time
import sys
import argparse
import signal
import shlex

class NodeControl():

    """
    This class represents a PLC or SCADA node. All of these devices have the same pattern of launching a tcpdump process in
    the eth0 interface, launching a plc_n.py script or scada.py script and when receives a SIGINT or SIGTERM signal store the recevied values into a .csv file.
    In addition, a pcap file is created with the tcpdump results
    """

    def sigint_handler(self, sig, frame):
        self.terminate()
        sys.exit(0)

    def terminate(self):
        """
        All the subprocesses launched in this Digital Twin follow the same pattern to ensure that they finish before continuing with the finishing of the parent process
        """
        print "Stopping Tcp dump process on PLC..."
        #self.process_tcp_dump.kill()

        self.process_tcp_dump.send_signal(signal.SIGINT)
        self.process_tcp_dump.wait()
        if self.process_tcp_dump.poll() is None:
            self.process_tcp_dump.terminate()
        if self.process_tcp_dump.poll() is None:
            self.process_tcp_dump.kill()

        print "Stopping PLC..."
        self.plc_process.send_signal(signal.SIGINT)
        self.plc_process.wait()
        if self.plc_process.poll() is None:
            self.plc_process.terminate()
        if self.plc_process.poll() is None:
            self.plc_process.kill()

    def main(self):
        """
        Main method of a device. The signal handler methods are define, the routing is configured
        (adding default gateways for the deviceS), a tcpdump process is started
        and a plc_n.py or scada.py script is launched
        :return:
        """
        args = self.get_arguments()
        self.process_arguments(args)

        signal.signal(signal.SIGINT, self.sigint_handler)
        signal.signal(signal.SIGTERM, self.sigint_handler)

        self.interface_name = self.name + '-eth0'
        self.delete_log()

        self.process_tcp_dump = self.start_tcpdump_capture()
        self.plc_process = self.start_plc()

        while self.plc_process.poll() is None:
            pass

        self.terminate()

    def process_arguments(self,arg_parser):
        if arg_parser.name:
            self.name = arg_parser.name
            print self.name
        else:
            self.name = 'plc1'

        if arg_parser.week:
            self.week_index = arg_parser.week
        else:
            self.week_index = 0

        if arg_parser.dict:
            self.dict_path = arg_parser.dict
        else:
            self.dict_path = 'plc_dicts.yaml'

        if arg_parser.attack_flag:
            self.attack_flag = True
            if arg_parser.attack_path:
                self.attack_path = arg_parser.attack_path
            else:
                self.attack_path = "../../attack_repository/attack_description.yaml"

            if arg_parser.attack_name:
                self.attack_name = arg_parser.attack_name
            else:
                self.attack_name = "plc_empty_tank_1"
        else:
            self.attack_flag = False
            self.attack_path = None
            self.attack_name = None

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

        cmd_string = 'python ' + self.name + '.py' + ' -w ' + str(self.week_index)

        if self.attack_flag:
            # Pass the path to the PLC so it can parse the attack information and run it
            cmd_string = 'python ' + self.name + '.py' + ' -w ' + str(self.week_index) + ' -f True -p ' + \
                         str(self.attack_path) + ' -a ' + str(self.attack_name)

        cmd = shlex.split(cmd_string)
        plc_process = subprocess.Popen(cmd, shell=False)
        return plc_process

    def get_arguments(self):
        parser = argparse.ArgumentParser(description='Master Script of a node in Minicps')
        parser.add_argument("--name", "-n", help="Name of the Mininet node and script to run")
        parser.add_argument("--week", "-w", help="Week index of the simulation")
        parser.add_argument("--dict", "-d", help="Dictionary of the PLCs logic")
        parser.add_argument("--attack_flag", "-f", help="Flag to indicate if this PLC needs to run an attack")
        parser.add_argument("--attack_path", "-p", help="Path to the attack repository")
        parser.add_argument("--attack_name", "-a", help="Name of the attack to be run by this PLC")
        return parser.parse_args()


if __name__ == "__main__":
    node_control = NodeControl()
    node_control.main()