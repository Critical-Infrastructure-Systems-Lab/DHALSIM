# MiniCPS Makefile

# VARIABLES {{{1

LATEST_VERSION = 1.1.3
MININET = sudo mn

PYTHON = sudo python
PYTHON_OPTS =

general-minitown:
	if [ ! -d general_topology/logs ]; then\
	   mkdir general_topology/logs;\
	fi
	if [ ! -d general_topology/output ]; then\
	   mkdir general_topology/output;\
	fi
	cd general_topology; rm -rf minitown_db.sqlite; $(PYTHON) $(PYTHON_OPTS) init.py; sudo chown mininet:mininet minitown_db.sqlite
	sudo pkill -f -u root "python -m cpppo.server.enip"
	sudo mn -c
	cd general_topology; sudo $(PYTHON) $(PYTHON_OPTS) automatic_run.py

single-minitown:
	if [ ! -d minitown_topology/logs ]; then\
	   mkdir minitown_topology/logs;\
	fi
	if [ ! -d minitown_topology/output ]; then\
	   mkdir minitown_topology/output;\
	fi
	cd minitown_topology; rm -rf minitown_db.sqlite; $(PYTHON) $(PYTHON_OPTS) init.py; sudo chown mininet:mininet minitown_db.sqlite
	sudo pkill -f -u root "python -m cpppo.server.enip"
	sudo mn -c
	cd minitown_topology; sudo $(PYTHON) $(PYTHON_OPTS) automatic_run.py

data-minitown:
	if [ ! -d minitown_topology_dataset_generation/logs ]; then\
	   mkdir minitown_topology_dataset_generation/logs;\
	fi
	if [ ! -d minitown_topology_dataset_generation/output ]; then\
	   mkdir minitown_topology_dataset_generation/output;\
	fi
	cd minitown_topology_dataset_generation; rm -rf minitown_db.sqlite; $(PYTHON) $(PYTHON_OPTS) init.py; sudo chown mininet:mininet minitown_db.sqlite
	sudo pkill  -f -u root "python -m cpppo.server.enip"
	sudo mn -c
	cd minitown_topology_dataset_generation; sudo $(PYTHON) $(PYTHON_OPTS) automatic_run.py

ctown:
	if [ ! -d ctown_topology/logs ]; then\
	   mkdir ctown_topology/logs;\
	fi
	if [ ! -d ctown_topology/output ]; then\
	   mkdir ctown_topology/output;\
	fi
	cd ctown_topology; rm -rf ctown_db.sqlite; $(PYTHON) $(PYTHON_OPTS) init.py; sudo chown mininet:mininet ctown_db.sqlite
	sudo pkill  -f -u root "python -m cpppo.server.enip"
	sudo mn -c
	cd ctown_topology; sudo $(PYTHON) $(PYTHON_OPTS) automatic_run.py

wadi:
	if [ ! -d wadi_topology/logs ]; then\
	   mkdir wadi_topology/logs;\
	fi
	if [ ! -d wadi_topology/output ]; then\
	   mkdir wadi_topology/output;\
	fi
	cd wadi_topology; rm -rf wadi_db.sqlite; $(PYTHON) $(PYTHON_OPTS) init.py; sudo chown mininet:mininet wadi_db.sqlite
	sudo pkill  -f -u root "python -m cpppo.server.enip"
	sudo mn -c
	cd wadi_topology; sudo $(PYTHON) $(PYTHON_OPTS) automatic_run.py

enhanced-ctown:
	if [ ! -d enhanced_ctown_topology/logs ]; then\
	   mkdir enhanced_ctown_topology/logs;\
	fi
	if [ ! -d enhanced_ctown_topology/output ]; then\
	   mkdir enhanced_ctown_topology/output;\
	fi
	cd enhanced_ctown_topology; rm -rf ctown_db.sqlite; $(PYTHON) $(PYTHON_OPTS) init.py; sudo chown mininet:mininet ctown_db.sqlite
	sudo pkill  -f -u root "python -m cpppo.server.enip"
	sudo mn -c
	cd enhanced_ctown_topology; sudo $(PYTHON) $(PYTHON_OPTS) automatic_run.py

general-ctown:
	if [ ! -d enhanced_ctown_topology/logs ]; then\
	   mkdir enhanced_ctown_topology/logs;\
	fi
	if [ ! -d enhanced_ctown_topology/output ]; then\
	   mkdir enhanced_ctown_topology/output;\
	fi
	cd enhanced_ctown_topology; rm -rf ctown_db.sqlite; $(PYTHON) $(PYTHON_OPTS) init.py; sudo chown mininet:mininet ctown_db.sqlite
	sudo pkill  -f -u root "python -m cpppo.server.enip"
	sudo mn -c
	cd enhanced_ctown_topology; sudo $(PYTHON) $(PYTHON_OPTS) general_automatic_run.py

clean-simulation:
	sudo pkill  -f -u root "python -m cpppo.server.enip"
	sudo mn -c

kill:
	sudo pkill python

finish-ctown: kill clean-simulation
