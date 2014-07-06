all: unittest check_convention

clean:
	rm -fr build dist dirbalak.egg-info

UNITTESTS=$(shell find py -name 'test_*.py' | sed 's@/@.@g' | sed 's/\(.*\)\.py/\1/' | sort)
COVERED_FILES=py/dirbalak/traverse.py
unittest:
	rm -f .coverage*
	PYTHONPATH=`pwd` COVERAGE_FILE=`pwd`/.coverage coverage run --parallel-mode --append -m unittest $(UNITTESTS)
	coverage combine
	coverage report --show-missing --rcfile=coverage.config --fail-under=100 --include='$(COVERED_FILES)'

check_convention:
	pep8 . --max-line-length=109

test-server:
	PYTHONPATH=py UPSETO_JOIN_PYTHON_NAMESPACES=yes python py/dirbalak/server/main.py $(ARGS)
