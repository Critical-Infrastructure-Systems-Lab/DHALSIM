#!/bin/bash
iptables -A PREROUTING -t nat -i $1-eth0 -p tcp --dport 44818 -j DNAT --to 192.168.1.1:44818
iptables -A FORWARD -p tcp -d 192.168.1.1 --dport 44818 -j ACCEPT
