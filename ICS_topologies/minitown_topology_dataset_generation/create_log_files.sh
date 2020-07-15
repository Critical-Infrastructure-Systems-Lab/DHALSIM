#!/bin/bash

files=(plc1 plc2 scada physical attacker_plc2 attacker_scada)

rm -rf output/*

for file in "${files[@]}"
  do
      touch output/$file".log"
done
