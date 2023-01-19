#!/bin/bash

for n in $(seq 1 154) ; do
	cp $1.yaml $1_$n.yaml
done
