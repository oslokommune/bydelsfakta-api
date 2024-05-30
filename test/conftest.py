import urllib

import boto3
import pytest
from moto import mock_aws

dataset_id = "boligpriser"
version = 1
parent_id = "bydelsfakta"


@pytest.fixture
def s3_client():
    with mock_aws():
        s3 = boto3.client("s3")
        yield s3


@pytest.fixture
def s3_bucket(s3_client):
    bucket = "ok-origo-dataplatform-test"
    s3_client.create_bucket(Bucket=bucket)
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
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, sdch",
            "Accept-Language": "en-US,en;q=0.8",
            "Cache-Control": "max-age=0",
            "CloudFront-Forwarded-Proto": "https",
            "CloudFront-Is-Desktop-Viewer": "true",
            "CloudFront-Is-Mobile-Viewer": "false",
            "CloudFront-Is-SmartTV-Viewer": "false",
            "CloudFront-Is-Tablet-Viewer": "false",
            "CloudFront-Viewer-Country": "US",
            "Host": "1234567890.execute-api.eu-west-1.amazonaws.com",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Custom User Agent String",
            "Via": "1.1 08f323deadbeefa7af34d5feb414ce27.cloudfront.net (CloudFront)",
            "X-Amz-Cf-Id": "cDehVQoZnx43VYQb9j2-nvCh-9z396Uhbp027Y2JvkCPNLmGJHqlaA==",
            "X-Forwarded-For": "127.0.0.1, 127.0.0.2",
            "X-Forwarded-Port": "443",
            "X-Forwarded-Proto": "https",
        },
        "requestContext": {
            "accountId": "123456789012",
            "authorizer": {"principalId": "service-account-bydelsfakta-frontend"},
            "resourceId": "123456",
            "stage": "prod",
            "requestId": "c6af9ac6-7b61-11e6-9a41-93e8deadbeef",
            "requestTime": "09/Apr/2015:12:34:56 +0000",
            "requestTimeEpoch": 1_428_582_896_000,
            "identity": {
                "cognitoIdentityPoolId": None,
                "accountId": None,
                "cognitoIdentityId": None,
                "caller": None,
                "accessKey": None,
                "sourceIp": "127.0.0.1",
                "cognitoAuthenticationType": None,
                "cognitoAuthenticationProvider": None,
                "userArn": None,
                "userAgent": "Custom User Agent String",
                "user": None,
            },
            "path": "/prod/path/to/resource",
            "resourcePath": "/{proxy+}",
            "httpMethod": "POST",
            "apiId": "1234567890",
            "protocol": "HTTP/1.1",
        },
    }


@pytest.fixture
def dataset_metadata():
    return {
        "Id": dataset_id,
        "processing_stage": "raw",
        "confidentiality": "green",
        "parent_id": parent_id,
    }


@pytest.fixture
def version_metadata():
    return [{"Id": f"{dataset_id}/{version}", "version": f"{version}"}]


@pytest.fixture
def version_metadata_old():
    return [{"versionID": f"{dataset_id}/{version}"}]


@pytest.fixture
def edition_metadata():
    return [
        {
            "Id": f"{dataset_id}/{version}/20190529T113052",
            "description": "Latest Edition",
            "edition": "2019-05-29T13:30:52+02:00",
            "endTime": "2017-12-31T23:00:00+01:00",
            "startTime": "2004-01-01T00:00:00+01:00",
        },
        {
            "description": "Old Edition",
            "edition": "2019-04-29T13:30:52+02:00",
            "Id": f"{dataset_id}/{version}/20190429T113052",
            "endTime": "2017-12-31T23:00:00+01:00",
            "startTime": "2004-01-01T00:00:00+01:00",
        },
    ]


@pytest.fixture
def s3_prefix():
    return urllib.parse.unquote_plus(
        f"raw/green/{parent_id}/{dataset_id}/version%3D1/edition%3D20190529T113052/"
    )
