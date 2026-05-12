.DEV_PROFILE := databrikker-dev
.PROD_PROFILE := databrikker-prod

GLOBAL_PY := python3
BUILD_VENV ?= .build_venv
BUILD_PY := $(BUILD_VENV)/bin/python

SAM_DIR := sam/api

.PHONY: init
init: $(BUILD_VENV)

$(BUILD_VENV):
	$(GLOBAL_PY) -m venv $(BUILD_VENV)
	$(BUILD_PY) -m pip install -U pip

.PHONY: format
format: $(BUILD_VENV)/bin/black
	$(BUILD_PY) -m black .

.PHONY: test
test: $(BUILD_VENV)/bin/tox
	$(BUILD_PY) -m tox -p auto -o

.PHONY: build
build:
	cd $(SAM_DIR) && sam build

.PHONY: deploy
deploy: login-dev init format test build
	@echo "\nDeploying to stage: dev\n"
	$(MAKE) _sam-deploy CONFIG_ENV=dev WORKSPACE=bydelsfakta SSM_ENV=padda-dev AWS_PROFILE=$(.DEV_PROFILE)

.PHONY: deploy-prod
deploy-prod: login-prod init format is-git-clean test build
	@echo "\nDeploying to stage: prod\n"
	$(MAKE) _sam-deploy CONFIG_ENV=prod WORKSPACE=bydelsfakta-prod SSM_ENV=padda-prod AWS_PROFILE=$(.PROD_PROFILE)

# Internal target: looks up gold-volume config, permission boundary ARN, the
# CFN service role ARN, and the SAM artifacts bucket from SSM, then runs sam
# deploy with the values as parameter overrides.
.PHONY: _sam-deploy
_sam-deploy:
	$(eval BUCKET := $(shell aws ssm get-parameter --profile $(AWS_PROFILE) --name /$(SSM_ENV)/bydelsfakta/gold-volume/bucket --query Parameter.Value --output text))
	$(eval PREFIX := $(shell aws ssm get-parameter --profile $(AWS_PROFILE) --name /$(SSM_ENV)/bydelsfakta/gold-volume/prefix --query Parameter.Value --output text))
	$(eval KMS_KEY := $(shell aws ssm get-parameter --profile $(AWS_PROFILE) --name /$(SSM_ENV)/bydelsfakta/gold-volume/kms-key-arn --query Parameter.Value --output text))
	$(eval BOUNDARY := $(shell aws ssm get-parameter --profile $(AWS_PROFILE) --name /$(SSM_ENV)/bydelsfakta/lambda-permissions-boundary-arn --query Parameter.Value --output text))
	$(eval CFN_ROLE := $(shell aws ssm get-parameter --profile $(AWS_PROFILE) --name /$(SSM_ENV)/bydelsfakta/sam/cfn-role-arn --query Parameter.Value --output text))
	$(eval ARTIFACTS := $(shell aws ssm get-parameter --profile $(AWS_PROFILE) --name /$(SSM_ENV)/bydelsfakta/sam/artifacts-bucket --query Parameter.Value --output text))
	$(eval GIT_REV := $(shell git rev-parse --abbrev-ref HEAD):$(shell git rev-parse --short HEAD))
	cd $(SAM_DIR) && sam deploy --config-env $(CONFIG_ENV) --profile $(AWS_PROFILE) \
	  --s3-bucket $(ARTIFACTS) \
	  --role-arn $(CFN_ROLE) \
	  --parameter-overrides \
	    WorkspaceName=$(WORKSPACE) \
	    S3Bucket=$(BUCKET) \
	    S3Prefix=$(PREFIX) \
	    KmsKeyArn=$(KMS_KEY) \
	    PermissionsBoundaryArn=$(BOUNDARY) \
	    GitRev=$(GIT_REV)

.PHONY: undeploy
undeploy: login-dev
	@echo "\nUndeploying stage: dev\n"
	aws cloudformation delete-stack --stack-name bydelsfakta-api --profile $(.DEV_PROFILE)

.PHONY: undeploy-prod
undeploy-prod: login-prod
	@echo "\nUndeploying stage: prod\n"
	aws cloudformation delete-stack --stack-name bydelsfakta-prod-api --profile $(.PROD_PROFILE)

.PHONY: login-dev
login-dev:
	aws sts get-caller-identity --profile $(.DEV_PROFILE) || aws sso login --profile=$(.DEV_PROFILE)

.PHONY: login-prod
login-prod:
	aws sts get-caller-identity --profile $(.PROD_PROFILE) || aws sso login --profile=$(.PROD_PROFILE)

.PHONY: is-git-clean
is-git-clean:
	@status=$$(git fetch origin && git status -s -b) ;\
	if test "$${status}" != "## main...origin/main"; then \
		echo; \
		echo Git working directory is dirty, aborting >&2; \
		false; \
	fi

###
# Python build dependencies
##

$(BUILD_VENV)/bin/%: $(BUILD_VENV)
	$(BUILD_PY) -m pip install -U $*
