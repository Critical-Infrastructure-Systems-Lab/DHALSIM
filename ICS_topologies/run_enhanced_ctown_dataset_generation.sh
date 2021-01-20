#!/bin/bash

for i in {0..30}
do
	if [ ! -d enhanced_ctown_topology/logs ]; then\
	   mkdir logs;\
	fi
	if [ ! -d enhanced_ctown_topology/output ]; then\
	   mkdir output;\
	fi
	cd enhanced_ctown_topology; rm -rf ctown_db.sqlite; python init.py; sudo chown mininet:mininet ctown_db.sqlite
	sudo pkill  -f -u root "python -m cpppo.server.enip"
	sudo mn -c
	sudo python automatic_run.py $i

	sudo pkill  -f -u root "python -m cpppo.server.enip"
	sudo mn -c
done
