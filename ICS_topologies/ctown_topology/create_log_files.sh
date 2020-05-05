#!/bin/bash

files=(plc1 plc2 plc3 plc4 plc5 plc6 plc7 plc9 scada physical)

rm -rf output/$file".log"

for file in "${files[@]}"
  do
      touch output/$file".log"
done
