import json
import os
import urllib

import boto3
from moto import mock_s3
from pytest import fixture

stage = "test"
m_url = "https://metadata.com/{}".format(stage)
os.environ["METADATA_API_URL"] = m_url
os.environ["STAGE"] = stage
import main

version_metadata = [
    {
        "datasetID": "boligpriser_historic-4owcY",
        "version": "1",
        "versionID": "1-zV86jpeY",
    }
]
edition_metadata = [
    {
        "datasetID": "boligpriser_historic-4owcY",
        "description": "Manually uploaded file",
        "edition": 1_551_107_009,
        "editionID": "EDITION-HAkZy",
        "endTime": "2017-12-31T23:00:00+01:00",
        "startTime": "2004-01-01T00:00:00+01:00",
        "versionID": "1-zV86jpeY",
    }
]


class Test:
    base_key = "processed/green/boligpriser_historic-4owcY/version%3D1-zV86jpeY/edition%3DEDITION-HAkZy/"

    def test_main_handler(self, requests_mock, s3_client, s3_bucket):
        for i in range(0, 19):
            s3_client.put_object(
                Bucket=s3_bucket,
                Key="{}{}.json".format(
                    urllib.parse.unquote_plus(self.base_key), f"{i:02}"
                ),
                Body=json.dumps({"number": f"{i:02}"}),
            )

        requests_mock.get(
            m_url + "/datasets/boligpriser_historic-4owcY/versions",
            text=json.dumps(version_metadata),
        )
        requests_mock.get(
            m_url
            + "/datasets/boligpriser_historic-4owcY/versions/{}/editions".format(
                version_metadata[0]["versionID"]
            ),
            text=json.dumps(edition_metadata),
        )

        result = main.latest_edition(event, {})
        assert result["statusCode"] == 200
        assert json.loads(result["body"])[1] == {"number": "08"}


@fixture
def s3_client():
    with mock_s3():
        s3 = boto3.client("s3")
        yield s3


@fixture
def s3_bucket(s3_client):
    bucket = "ok-origo-dataplatform-test"
    s3_client.create_bucket(Bucket=bucket)
    return bucket


event = {
    "body": "eyJ0ZXN0IjoiYm9keSJ9",
    "resource": "/{dataset}",
    "path": "/",
    "httpMethod": "GET",
    "queryStringParameters": {"geography": "02,08,12"},
    "pathParameters": {"dataset": "boligpriser_historic-4owcY"},
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
