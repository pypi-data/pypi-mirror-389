# Makefile for zapf.

SHELL = /bin/bash

T = test
PYTHON = python
JENKINS_HOST ?= jenkins.admin.frm2.tum.de

test:
	$(PYTHON) -m pytest -v $(O) $(T)

test-coverage:
	$(PYTHON) -m pytest -v --cov --cov-report=html --cov-report=term $(O) $(T)

clean:
	rm -rf .coverage
	find . -name '*.pyc' -exec rm -f {} \;

# doc:
# 	cd doc && $(MAKE) html

.PHONY: test test-coverage lint clean jenkinslint doc

release-patch:
	MODE="patch" $(MAKE) release

release-minor:
	MODE="minor" $(MAKE) release

release:
	ssh $(JENKINS_HOST) -p 29417 build -v -s -p GERRIT_PROJECT=$(shell git config --get remote.origin.url | rev | cut -d '/' -f -3 | rev) -p ARCH=all -p MODE=$(MODE) ReleasePipeline

.PHONY: release release-patch release-minor
