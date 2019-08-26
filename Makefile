.AWS_ROLE_NAME ?= oslokommune/iamadmin-SAML

.DEV_ACCOUNT := ***REMOVED***
.PROD_ACCOUNT := ***REMOVED***

.DEV_ROLE := 'arn:aws:iam::$(.DEV_ACCOUNT):role/$(.AWS_ROLE_NAME)'
.PROD_ROLE := 'arn:aws:iam::$(.PROD_ACCOUNT):role/$(.AWS_ROLE_NAME)'

.DEV_PROFILE := saml-origo-dev
.PROD_PROFILE := saml-dataplatform-prod

.PHONY: init
init:
	npm install

.PHONY: test
test:
	python3 -m tox -p auto

.PHONY: deploy
deploy: init format test login-dev
	sls deploy --stage dev --aws-profile $(.DEV_PROFILE)
	$(MAKE) update-ssm-dev

.PHONY: deploy-prod
deploy-prod: init format is-git-clean test login-prod
	sls deploy --stage prod --aws-profile $(.PROD_PROFILE)
	$(MAKE) update-ssm-prod

.PHONY: login-dev
login-dev:
	saml2aws login --role=$(.DEV_ROLE) --profile=$(.DEV_PROFILE)

.PHONY: login-prod
login-prod:
	saml2aws login --role=$(.PROD_ROLE) --profile=$(.PROD_PROFILE)

.PHONY: is-git-clean
is-git-clean:
	@status=$$(git fetch origin && git status -s -b) ;\
	if test "$${status}" != "## master...origin/master"; then \
		echo; \
		echo Git working directory is dirty, aborting >&2; \
		false; \
	fi


.PHONY: format
format: init
	python3 -m black .


.PHONY: update-ssm-prod
update-ssm-prod:
	url=$$(sls info -s prod --verbose | grep ServiceEndpoint | cut -d' ' -f2) &&\
	aws --region eu-west-1 ssm put-parameter --overwrite \
	--profile=$(.PROD_PROFILE) \
	--cli-input-json "{\"Type\": \"String\", \"Name\": \"/dataplatform/bydelsfakta-api/url\", \"Value\": \"$$url\"}"

.PHONY: update-ssm-dev
update-ssm-dev: login-dev
	url=$$(sls info -s dev --verbose | grep ServiceEndpoint | cut -d' ' -f2) &&\
	aws --region eu-west-1 ssm put-parameter --overwrite \
	--profile=$(.DEV_PROFILE) \
	--cli-input-json "{\"Type\": \"String\", \"Name\": \"/dataplatform/bydelsfakta-api/url\", \"Value\": \"$$url\"}"