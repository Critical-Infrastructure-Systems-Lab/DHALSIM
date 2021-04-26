#!/bin/bash
iptables -t nat -v -L PREROUTING
iptables -L FORWARD
iptables -t nat -v -L POSTROUTING
