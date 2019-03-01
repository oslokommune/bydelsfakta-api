.PHONY: init
init:
	python3 -m pip install tox black pip-tools
	pip-compile

.PHONY: format
format: init
	python3 -m black main.py test_main.py setup.py

.PHONY: deploy
deploy: format
	python3 -m tox -p auto && \
	sls deploy && \
	sls downloadDocumentation --outputFileName swagger.yaml