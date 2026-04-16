import os

import boto3
import pytest
from moto import mock_aws

dataset_id = "boligpriser"


@pytest.fixture
def s3_client():
    with mock_aws():
        s3 = boto3.client("s3")
        yield s3


@pytest.fixture
def s3_bucket(s3_client):
    bucket = os.environ["S3_BUCKET"]
    s3_client.create_bucket(
        Bucket=bucket,
        CreateBucketConfiguration={"LocationConstraint": os.environ["AWS_REGION"]},
    )
    return s3_client, bucket


@pytest.fixture
def event():
    return {
        "body": "eyJ0ZXN0IjoiYm9keSJ9",
        "resource": "/{dataset}",
        "path": "/",
        "httpMethod": "GET",
        "queryStringParameters": {"geography": "02,08,12"},
        "pathParameters": {"dataset": f"{dataset_id}"},
        "stageVariables": {},
        "headers": {
            "Accept": "text/html",
            "Host": "1234567890.execute-api.eu-west-1.amazonaws.com",
        },
        "requestContext": {
            "accountId": "123456789012",
            "resourceId": "123456",
            "stage": "prod",
            "requestId": "c6af9ac6-7b61-11e6-9a41-93e8deadbeef",
        },
    }
