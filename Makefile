.PHONY: init
init:
	python3 -m pip install tox black pip-tools yq
	pip-compile

.PHONY: format
format: init
	python3 -m black main.py test_main.py setup.py --line-length 160

.PHONY: test
test: init
	python3 -m tox -p auto

.PHONY: deploy
deploy: test
	sls deploy

.PHONY: deploy-prod
deploy-prod: test
	sls deploy --stage prod && \
	sls downloadDocumentation --outputFileName swagger.yaml --stage prod

.PHONY: put-parameter
put-parameter: init
	url=$$(sls info --verbose | grep -Ev "Stack Outputs|Service Information" | yq .ServiceEndpoint) &&\
	aws --region eu-west-1 ssm put-parameter \
	--name "/dataplatform/bydelsfakta-api/url" \
	--value $$url \
	--type "String" \
	--overwrite

echo:
	@echo "HELLO"