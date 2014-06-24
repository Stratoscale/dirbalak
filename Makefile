all: unittest check_convention

clean:
	rm -fr build dist dirbalak.egg-info

UNITTESTS=$(shell find tests -name 'test*.py' | sed 's@/@.@g' | sed 's/\(.*\)\.py/\1/' | sort)
COVERED_FILES=dirbalak/*.py
unittest:
	rm -f .coverage*
	PYTHONPATH=`pwd` COVERAGE_FILE=`pwd`/.coverage coverage run --parallel-mode --append -m unittest $(UNITTESTS)
	coverage combine
	coverage report --show-missing --rcfile=coverage.config --fail-under=86 --include='$(COVERED_FILES)'

check_convention:
	pep8 . --max-line-length=109

uninstall:
	-yes | sudo pip uninstall dirbalak
	sudo rm /usr/bin/dirbalak

install:
	-yes | sudo pip uninstall dirbalak
	python setup.py build
	python setup.py bdist
	sudo python setup.py install
	sudo cp dirbalak.sh /usr/bin/dirbalak
	sudo chmod 755 /usr/bin/dirbalak
