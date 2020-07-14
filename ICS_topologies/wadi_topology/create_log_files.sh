#!/bin/bash

files=(plc1 plc2 physical attacker scada)

rm -rf output/*

for file in "${files[@]}"
  do
      touch output/$file".log"
done