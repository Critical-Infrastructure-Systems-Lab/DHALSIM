#!/bin/bash

# There should be a DHALSIM configuration file with .yaml extension in the same folder. Also a .inp and .cpa files
# with the same name in this folder
topology_name=$1
week_index=$2
folder_name=$topology_name"_topology"

# Create log folder
if [ ! -d "logs" ]; then\
   mkdir "logs";\
fi

# Output folder to store the experiment results
if [ ! -d "output" ]; then\
   mkdir "output";\
fi

rm -rf plant.sqlite; sudo python init.py; sudo chown mininet:mininet plant.sqlite
sudo pkill  -f -u root "python -m cpppo.server.enip"
chmod +x *.sh
sudo mn -c
sudo python automatic_run.py -c $topology_name".yaml" $week_index
