#!/bin/bash
files=(plc1 plc2 scada physical)
rm -rf output/*
for file in "${files[@]}"
 do
 touch output/$file".log"
done

