#!/bin/bash
iNIC=r1-eth1
oNIC=r0-eth0

# -m extend the packet matching module with module conntrack
# conntrack This module, when combined with connection tracking, allows access to more
# connection tracking information than the "state" match. (this module is present only if
# iptables was compiled under a kernel supporting this feature)
# ctstate is the state to be matched, NEW means the packet has started a new connection, or otherwise associated with a connection which has not seen packets in both directions
sudo iptables -A FORWARD -o $oNIC -i $iNIC -s 192.168.1.1 -m conntrack --ctstate NEW -j ACCEPT
sudo iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
sudo iptables -t nat -F POSTROUTING # flushes this chain, to ensure postrouting is empty
sudo iptables -t nat -A POSTROUTING -o $oNIC -j MASQUERADE

sudo sh -c "echo 1 > /proc/sys/net/ipv4/ip_forward"
