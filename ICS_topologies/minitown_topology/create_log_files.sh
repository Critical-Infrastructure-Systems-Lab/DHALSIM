#!/bin/bash

files=(plc1 plc2 scada physical)

for file in "${files[@]}"
  do
      touch $file".log"
done
