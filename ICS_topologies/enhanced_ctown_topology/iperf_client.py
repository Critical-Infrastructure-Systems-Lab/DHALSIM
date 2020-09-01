import subprocess
import argparse
import signal
import sys

class IperfClient():

    def interrupt(self, sig, frame):
        """
        This method is provided by the signal python library. We call the finish method that interrupts, terminates, or kills the simulation and exit
        """
        sys.exit(0)

    def main(self):
        signal.signal(signal.SIGINT, self.interrupt)
        signal.signal(signal.SIGTERM, self.interrupt)
        args = self.get_arguments()
        self.process_arguments(args)

        self.iperf = self.start_iperf_client()

        while self.iperf.poll() is None:
            pass

    def process_arguments(self,arg_parser):
        if arg_parser.connect:
            self.connect = arg_parser.connect
        else:
            self.connect = '127.0.0.1'

        if arg_parser.parallel:
            self.parallel = arg_parser.parallel
        else:
            self.parallel = str(1)

        if arg_parser.time:
            self.time = arg_parser.time
        else:
            self.time = str(10)

        if arg_parser.bandwidth:
            self.bandwidth = arg_parser.bandwidth
        else:
            self.bandwidth = None


    def get_arguments(self):
        parser = argparse.ArgumentParser(description='Script to launch an iperf3 client')
        parser.add_argument("--connect", "-c",help="IP address of server to connect. Default is localhost")
        parser.add_argument("--parallel", "-P", help="Number of parallel connections. Default is 1")
        parser.add_argument("--time", "-t", help="Time of the iperf test in seconds. Default is 10 seconds")
        parser.add_argument("--bandwidth", "-b", help="Max bandwidth to be used by the client in n bits/sec. Default is unlimited")
        return parser.parse_args()

    def start_iperf_client(self):
        if self.bandwidth:
            iperf = subprocess.Popen(['iperf3', '-c', self.connect, '-P', self.parallel, '-t', self.time, '-b', self.bandwidth], shell=False)
        else:
            iperf = subprocess.Popen(['iperf3', '-c', self.connect, '-P', self.parallel, '-t', self.time], shell=False)
        return iperf

if __name__ == "__main__":
    iperf_client = IperfClient()
    iperf_client.main()
