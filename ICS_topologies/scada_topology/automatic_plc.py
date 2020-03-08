import subprocess
import time
import sys
import argparse

class NodeControl():
    def main(self):
        args = self.get_arguments()
        self.process_arguments(args)
        self.configure_routing()
        self.delete_log()
        process_tcp_dump = self.start_tcpdump_capture()

        plc = self.start_plc()
        plc.wait()
        print "Stopping PLC1..."
        process_tcp_dump.kill()

    def process_arguments(self,arg_parser):
        if arg_parser.name:
            self.name = arg_parser.name
        else:
            self.name = 'plc1'

    def delete_log(self):
        subprocess.call(['rm', '-rf', self.name + '.log'])

    def configure_routing(self):
        self.interface_name = self.name + '-eth0'
        routing = subprocess.call(['route','add','default', 'gw' ,'192.168.1.254', self.interface_name], shell=False)
        return routing

    def start_tcpdump_capture(self):
        pcap = self.interface_name+'.pcap'
        tcp_dump = subprocess.Popen(['tcpdump', '-i', self.interface_name, '-w', pcap], shell=False)
        return tcp_dump

    def start_plc(self):
        plc_process = subprocess.Popen(['python', self.name + '.py'], shell=False)
        return plc_process

    def get_arguments(self):
        parser = argparse.ArgumentParser(description='Master Script of a node in Minicps')
        parser.add_argument("--name", "-n",help="Name of the mininet node and script to run")
        return parser.parse_args()

if __name__=="__main__":
    node_control = NodeControl()
    node_control.main()