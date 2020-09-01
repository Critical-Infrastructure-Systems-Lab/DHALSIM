import subprocess
import argparse
import signal
import sys

class IperfServer():

    def main(self):
        signal.signal(signal.SIGINT, self.interrupt)
        signal.signal(signal.SIGTERM, self.interrupt)
        self.iperf = self.start_iperf_server()

        while self.iperf.poll() is None:
            pass

    def interrupt(self, sig, frame):
        """
        This method is provided by the signal python library. We call the finish method that interrupts, terminates, or kills the simulation and exit
        """
        sys.exit(0)

    def start_iperf_server(self):
        iperf = subprocess.Popen(['iperf3', '-s'], shell=False)
        return iperf

if __name__=="__main__":
    iperf_server = IperfServer()
    iperf_server.main()