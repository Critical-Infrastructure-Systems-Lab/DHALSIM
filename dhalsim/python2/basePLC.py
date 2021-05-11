from minicps.devices import PLC
import csv
import signal
import sys

import thread
import threading
import shlex
import subprocess

class BasePLC(PLC):

    def send_system_state(self, a, b):
        """
        This method sends the values to the SCADA server or any other client requesting the values
        :param a:
        :param b:
        :return:
        """
        while self.reader:
            values = []
            for tag in self.tags:
                with self.lock:
                    values.append(self.get(tag))
            self.send_multiple(self.tags, values, self.send_adddress)

    def set_parameters(self, tags, values, reader, lock, send_address, week_index=0):

        self.tags = tags
        self.values = values
        self.reader = reader
        self.lock = lock
        self.send_adddress = send_address
        self.week_index = week_index

    def sigint_handler(self, sig, frame):
        print('DEBUG plc shutdown')
        self.reader = False
        sys.exit(0)

    def startup(self):
        signal.signal(signal.SIGINT, self.sigint_handler)
        signal.signal(signal.SIGTERM, self.sigint_handler)

        thread.start_new_thread(self.send_system_state,(0,0))