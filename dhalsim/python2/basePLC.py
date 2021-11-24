import signal
import sys
import time
import thread
import numpy as np
from minicps.devices import PLC


class BasePLC(PLC):

    # Pulls a fresh value from the local DB and updates the local CPPPO
    def send_system_state(self):
        values = []
        # Send sensor values (may have gaussian noise)
        for tag in self.sensors:
            # noinspection PyBroadException
            try:
                # Gaussian noise added with respect to noise_scale
                if self.noise_scale != 0:
                    values.append(float(self.get(tag)) + np.random.normal(0, self.noise_scale))
                else:
                    values.append(float(self.get(tag)))
            except Exception:
                self.logger.error("Exception trying to get the tag.")
                continue
        # Send actuator values (unaffected by noise)
        for tag in self.actuators:
            # noinspection PyBroadException
            try:
                values.append(self.get(tag))
            except Exception:
                self.logger.error("Exception trying to get the tag.")
                continue

        self.send_multiple(self.tags, values, self.send_adddress)

    def set_parameters(self, sensors, actuators, values, send_address, noise_scale, week_index=0):
        self.sensors = sensors
        self.actuators = actuators
        self.tags = self.sensors + self.actuators
        self.values = values
        self.send_adddress = send_address
        self.noise_scale = noise_scale
        self.week_index = week_index

    def sigint_handler(self, sig, frame):
        self.logger.debug('PLC shutdown commencing.')
        self.reader = False
        sys.exit(0)

    def startup(self):
        signal.signal(signal.SIGINT, self.sigint_handler)
        signal.signal(signal.SIGTERM, self.sigint_handler)
        #thread.start_new_thread(self.send_system_state, (0, 0))