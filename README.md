# Bydelsfakta API

AWS Lambda + API Gateway that serves bydelsfakta JSON datasets from S3 based on
geography codes.

## Endpoint

```
GET /{dataset}?geography=01,02,...
```

The handler parses two-digit geography codes from the `geography` query
parameter and returns matching `{prefix}{dataset}/{geo}.json` objects from S3 as
a JSON array.

## Layout

- `sam/api/template.yaml` — SAM template (Lambda + API Gateway).
- `sam/api/src/` — Lambda source (`app.py` is the entry point).
- `sam/api/samconfig.toml` — per-stage deploy config.
- `test/` — `pytest` + `moto` tests for the handler.

## Setup

1. Install [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html).
2. Install Python toolchain: `python3 -m pip install --user tox black`
   (add `$HOME/.local/bin` to `$PATH`).

## Formatting code

Code is formatted using [black](https://pypi.org/project/black/): `make format`

## Running tests

Tests are run using [tox](https://pypi.org/project/tox/): `make test`

For tests and linting we use [pytest](https://pypi.org/project/pytest/),
[flake8](https://pypi.org/project/flake8/) and
[black](https://pypi.org/project/black/).

## Deploy

CI/CD runs from `.github/workflows/deploy-{dev,prod}.yml` on push to `main`.
The workflow resolves all deploy parameters from SSM, then runs `sam build` and
`sam deploy` against the CloudFormation service role created by `padda-iac`.

The CloudFormation stack is `bydelsfakta-api` (dev) / `bydelsfakta-prod-api`
(prod). The API Gateway stage is `v1`, so the endpoint URL is
`https://{api-id}.execute-api.eu-west-1.amazonaws.com/v1/{dataset}`.

Local deploy (rarely needed):

```
make deploy       # dev
make deploy-prod  # prod (refuses to run on a dirty working tree)
```

## Configuration

The Lambda reads gold-layer JSON files directly from the S3 location backing the
`gold_output` Unity Catalog volume in the `dig-bydelsfakta` catalog. The volume
itself is defined in the sister repo `bydelsfakta-databricks`.

The deploy parameters — S3 bucket, S3 prefix, KMS key ARN, Lambda permission
boundary ARN, and the SAM CloudFormation service role ARN — are read at deploy
time from SSM parameters under `/padda-{dev,prod}/bydelsfakta/`. Those
parameters are written by the `padda-iac` Terraform stacks
`workspace-bydelsfakta` (dev) and `workspace-bydelsfakta-prod` (prod). Update
those if the bucket, KMS key, volume, or IAM resources change.
