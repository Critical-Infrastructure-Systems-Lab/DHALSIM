#!/bin/bash

files=(plc1 plc2 plc3 plc4 plc5 plc6 plc7 plc9 scada physical)

for file in "${files[@]}"
  do
      rm -rf output/$file".log"
      touch output/$file".log"
done
