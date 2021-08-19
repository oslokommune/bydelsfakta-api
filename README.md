Bydelsfakta-api
=============

Fetches the latest edition of given dataset.


The api fetches bydelsfakta data based on geography.

## Setup

1. Install [Serverless Framework](https://serverless.com/framework/docs/getting-started/)
2. Install Serverless plugins: `make init`
3. Install Python toolchain: `python3 -m pip install (--user) tox black pip-tools`
   - If running with `--user` flag, add `$HOME/.local/bin` to `$PATH`

## Formatting code

Code is formatted using [black](https://pypi.org/project/black/): `make format`

## Running tests

Tests are run using [tox](https://pypi.org/project/tox/): `make test`

For tests and linting we use [pytest](https://pypi.org/project/pytest/), [flake8](https://pypi.org/project/flake8/) and [black](https://pypi.org/project/black/).

## Deploy

Deploy to dev is automatic via GitHub Actions, while deploy to prod can be triggered with GitHub Actions via dispatch. You can alternatively deploy from local machine (requires `saml2aws`) with: `make deploy` or `make deploy-prod`.

## Input

Optional parameter geography, e.g. `geography=01`

## Output

The function returns the data from a bydelsfakta. 
