import cip # library that has the packet structure of minicps network data
from scapy.all import * # scapy python is a tool to disect network packets
from scapy.contrib import modbus
import pandas as pd
from decimal import Decimal
import time
import sys
from scapy.layers.inet import IP
from scapy.layers.inet import TCP
from scapy.all import Ether
from scapy.all import *
import re

test = rdpcap("test.pcap")
packet = test[int(sys.argv[1])]

start = time.time()

sender_context = packet['ENIP_TCP'].sender_context
text = str(test[69]['CIP_ReqConnectionManager'].message.path)
path = re.findall(r"'(.*?)'", text)[0]

end = time.time()

print("Sender context is: " + str(sender_context))
print("Path is: " + str(path))
print("Execution time: " + str(end - start))
