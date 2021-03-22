#!/bin/bash 
if [ ! -d week_$1 ]; then
	mkdir week_$1;
fi
echo "Copying to " week_$1

cp output/* week_$1