from minicps.devices import PLC
import csv
import signal
import sys

import threading
import shlex
import subprocess
import time

class BasePLC(PLC):

    def send_system_state(self):
        """
        This method sends the values to the SCADA server or any other client requesting the values
        :return:
        """
        while self.reader:
            values = []
            for tag in self.tags:
                with self.lock:
                    # noinspection PyBroadException
                    try:
                        values.append(self.get(tag))
                    except Exception:
                        print "Exception trying to get the tag"
                        time.sleep(0.05)
                        continue
                    values.append(self.get(tag))
            self.send_multiple(self.tags, values, self.send_adddress)
            time.sleep(0.05)

    def set_parameters(self, path, result_list, tags, values, reader, lock, send_address, lastPLC=False, week_index=0, isScada=False):

        self.result_list = result_list
        self.path = path
        self.tags = tags
        self.values = values
        self.reader = reader
        self.lock = lock
        self.send_adddress = send_address
        self.lastPLC = lastPLC
        self.week_index = week_index
        self.isScada = isScada

    def write_output(self):
        with open('output/' + self.path, 'w') as f:
            writer = csv.writer(f)
            writer.writerows(self.result_list)

    def sigint_handler(self, sig, frame):
        print 'DEBUG plc shutdown'
        self.reader = False
        self.write_output()
        if self.lastPLC:
            self.move_files()
        sys.exit(0)

    def move_files(self):
        cmd = shlex.split("./copy_output.sh " + str(self.week_index))
        subprocess.call(cmd)

    def startup(self):
        signal.signal(signal.SIGINT, self.sigint_handler)
        signal.signal(signal.SIGTERM, self.sigint_handler)

        if not self.isScada:
            threading.Thread(target=self.send_system_state).start()