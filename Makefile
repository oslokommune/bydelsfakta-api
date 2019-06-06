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
	sls deploy

.PHONY: deploy-prod
deploy-prod: test
	sls deploy --stage prod && \
	sls downloadDocumentation --outputFileName swagger.yaml --stage prod

.PHONY: update-ssm
update-ssm:
	url=$$(sls info -s $$STAGE --verbose | grep ServiceEndpoint | cut -d' ' -f2) &&\
	aws --region eu-west-1 ssm put-parameter --overwrite \
	--cli-input-json "{\"Type\": \"String\", \"Name\": \"/dataplatform/bydelsfakta-api/url\", \"Value\": \"$$url\"}"

echo:
	@echo "HELLO"