#!/bin/bash

files=(plc1 plc2 plc3 plc4 plc5 plc6 plc7 plc8 plc9 physical attacker arp_poison scada client server)

rm -rf output/*

for file in "${files[@]}"
  do
      touch output/$file".log"
done
