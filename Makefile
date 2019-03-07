.PHONY: init
init:
	python3 -m pip install tox black pip-tools
	pip-compile

.PHONY: format
format: init
	python3 -m black main.py test_main.py setup.py --line-length 160

.PHONY: test
test: init
	python3 -m tox -p auto

.PHONY: deploy
deploy: test
	sls deploy && \
	sls downloadDocumentation --outputFileName swagger.yaml