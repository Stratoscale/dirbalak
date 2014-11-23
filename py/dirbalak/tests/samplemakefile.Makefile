all: build test rpm whiteboxtest docs

LOGCONF = $(PWD)/py/strato/snld/logconf.json

docs: build/doxygen.errors

build/doxygen.errors: include/strato/netlib.h
	- mkdir -p build
	doxygen interface.doxyfile 2> build/doxygen.errors
	@test -s build/doxygen.errors || ( @echo "ERROR: Doxygen reports documentation errors" exit 1 )
	@echo "Doxygen documentation generated successfully"

clean: clean_unittest
	rm -fr build

.PHONY: build
build:
	$(MAKE) -f build.Makefile

whiteboxtest: build
	UPSETO_JOIN_PYTHON_NAMESPACES=yes PYTHONPATH=$(PWD)/py:$(PWD)/../consulate:$(PWD)/../noded/testing PATH=$(PWD)/../noded/testing/qpidd:${PATH} LD_LIBRARY_PATH=$(PWD)/../noded/testing/qpidd:${LD_LIBRARY_PATH} STRATO_LOGS_CONFIGURATION_FILE=${LOGCONF} python ../pywhiteboxtest/runner $(REGEX)

racktest: build
	RACKATTACK_PROVIDER=tcp://localhost:1014@tcp://localhost:1015 UPSETO_JOIN_PYTHON_NAMESPACES=yes PYTHONPATH=.:py python ../pyracktest/runner $(REGEX)

submit:
	solvent submitproduct rpm build/rpm

check_convention:
	pep8 py whiteboxtest racktests --max-line-length=109

export CXXTEST_FIND_ROOT = c
export UNITTEST_INCLUDES = -Iinclude -Ic -I.
export VOODOO_INCLUDES = --includePath=include --includePath=c
export VOODOO_ROOT_DIR = ../voodoo-mock
export ENFORCE_COVERAGE_FIND_PATTERN_CPP = c/netlib/send_task.h c/netlib/receive_task.h

include $(VOODOO_ROOT_DIR)/make/integrations/complete.Makefile

build/snld.egg: py/strato/snld/main.py build
	-mkdir -p $(@D)
	PYTHONPATH=$(PWD)/py:$(PWD)/../consulate:$(PWD)/../noded/testing python -m upseto.packegg --entryPoint=$< --output=$@ --createDeps=$@.deps --compile_pyc --joinPythonNamespaces
-include build/snld.egg.deps

NETLIB_RPMBUILD_ROOT = $(HOME)/rpmbuild/snld
build/rpm/strato-snld-1-0.x86_64.rpm: rpm/snld.spec rpm/strato-snld.service build/snld.egg
	-mkdir -p $(@D)
	cd rpm ; TOP=$(PWD) rpmbuild -ba -vv --define "_topdir $(NETLIB_RPMBUILD_ROOT)" *.spec
	cp $(NETLIB_RPMBUILD_ROOT)/RPMS/x86_64/$(notdir $(@)) $(@D)
	rm -rf $(NETLIB_RPMBUILD_ROOT)

.PHONY: rpm
rpm: build/rpm/strato-snld-1-0.x86_64.rpm

prepareForCleanBuild:
	-yum erase --assumeyes zeromq-devel
	yum install --assumeyes zeromq3-devel python-oslo-config python-qpid qpid-cpp-server
	pip install oslo.messaging ioctl-opt
