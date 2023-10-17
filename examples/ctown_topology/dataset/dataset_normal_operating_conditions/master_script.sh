#!/bin/bash

for file in ./*.yaml
do
  echo running for $file
  sudo dhalsim $file
done
