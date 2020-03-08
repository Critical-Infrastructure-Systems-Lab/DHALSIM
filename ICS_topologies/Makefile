# MiniCPS Makefile

# VARIABLES {{{1

LATEST_VERSION = 1.1.3
MININET = sudo mn

PYTHON = sudo python
PYTHON_OPTS =

# regex testMatch: (?:^|[b_.-])[Tt]est)
# --exe: include also executable files
# -s: don't capture std output
# nosetests -s tests/devices_tests.py:fun_name

scada-mini:
	if [ ! -d scada_topology/logs ]; then\
	   mkdir scada_topology/logs;\
	fi
	cd scada_topology; rm -rf minitown_db.sqlite; $(PYTHON) $(PYTHON_OPTS) init.py; sudo chown mininet:mininet minitown_db.sqlite
	sudo pkill  -f -u root "python -m cpppo.server.enip"
	sudo mn -c
	cd scada_topology; $(PYTHON) $(PYTHON_OPTS) run.py

auto-mitm:
	if [ ! -d scada_topology/logs ]; then\
	   mkdir scada_topology/logs;\
	fi
	cd scada_topology; rm -rf minitown_db.sqlite; $(PYTHON) $(PYTHON_OPTS) init.py; sudo chown mininet:mininet minitown_db.sqlite
	sudo pkill  -f -u root "python -m cpppo.server.enip"
	sudo mn -c
	cd scada_topology; sudo $(PYTHON) $(PYTHON_OPTS) automatic_run.py

clean-simulation:
	sudo pkill  -f -u root "python -m cpppo.server.enip"
	sudo mn -c

