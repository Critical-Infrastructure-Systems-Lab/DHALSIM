#!/bin/bash
iptables -A PREROUTING -t nat -i $1-eth0 -p tcp --dport 80 -j DNAT --to 192.168.1.1:8080
iptables -A FORWARD -p udp -d 192.168.1.1 --dport 8080 -j ACCEPT
