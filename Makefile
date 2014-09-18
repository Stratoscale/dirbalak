all: build unittest check_convention

clean:
	rm -fr build

UNITTESTS=$(shell cd py; find -name 'test_*.py' | sed 's@/@.@g' | sed 's/^\.\.\(.*\)\.py/\1/' | sort)
COVERED_FILES=py/dirbalak/traverse.py
unittest:
	rm -f .coverage*
	PYTHONPATH=py UPSETO_JOIN_PYTHON_NAMESPACES=yes COVERAGE_FILE=`pwd`/.coverage coverage run --parallel-mode --append -m unittest $(UNITTESTS)
	coverage combine
	coverage report --show-missing --rcfile=coverage.config --fail-under=100 --include='$(COVERED_FILES)'

check_convention:
	pep8 . --max-line-length=109

test-server:
	RACKATTACK_PROVIDER=tcp://rackattack-provider:1014@tcp://rackattack-provider:1015 PYTHONPATH=py UPSETO_JOIN_PYTHON_NAMESPACES=yes python py/dirbalak/server/main.py --multiver /home/me/multiverse.yaml --unsecured --officialObjectStore=oberon:1010 --githubNetRCFile=/home/me/bamboo.netrc

.PHONY: build
build: build/dirbalakbuild.egg build/dirbalakserver.egg

build/dirbalakbuild.egg: py/dirbalak/main.py
build/dirbalakserver.egg: py/dirbalak/server/main.py
-include build/dirbalakbuild.egg.dep
-include build/dirbalakserver.egg.dep

build/%.egg:
	-mkdir $(@D)
	UPSETO_JOIN_PYTHON_NAMESPACES=yes PYTHONPATH=py:../realtimewebui/py python -m upseto.packegg --entryPoint=$< --output=$@ --createDeps=$@.dep --compile_pyc --joinPythonNamespaces

install: build
	-sudo systemctl stop dirbalak.service
	-sudo mkdir -p /usr/share/dirbalak/realtimewebui
	sudo cp build/*.egg /usr/share/dirbalak
	sudo cp -r html /usr/share/dirbalak/
	sudo cp -r js /usr/share/dirbalak/
	sudo cp -r static /usr/share/dirbalak/
	sudo cp -r ../realtimewebui/js ../realtimewebui/html ../realtimewebui/externals /usr/share/dirbalak/realtimewebui
	sudo cp dirbalak.service /usr/lib/systemd/system/dirbalak.service
	sudo systemctl enable dirbalak.service
	if ["$(DONT_START_SERVICE)" == ""]; then sudo systemctl start dirbalak; fi

uninstall:
	-sudo systemctl stop dirbalak
	-sudo systemctl disable dirbalak.service
	-sudo rm -fr /usr/lib/systemd/system/dirbalak.service
	sudo rm -fr /usr/share/dirbalak
