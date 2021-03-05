#!/bin/bash

for i in {27..30}
do
	echo "Running week " $i

	if [ ! -d minitown_topology/logs ]; then\
	   mkdir minitown_topology/logs;\
	fi

	if [ ! -d minitown_topology/output ]; then\
	   mkdir minitown_topology/output;\
	fi

	cd minitown_topology; rm -rf minitown_db.sqlite; python init.py; sudo chown mininet:mininet minitown_db.sqlite
	sudo pkill  -f -u root "python -m cpppo.server.enip"
	sudo mn -c
	sudo python automatic_run.py $i
done
