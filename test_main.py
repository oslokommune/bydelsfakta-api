import json
import urllib

from pytest import fixture

import main

import boto3
from moto import mock_s3
import pytest
import requests


base_key = 'processed%2Fgreen%2Fboligpriser_historic-4owcY%2Fversion%3D1-zV86jpeY%2Fedition%3DEDITION-HAkZy%2F'

version_metadata = [{
  "datasetID": "boligpriser_historic-4owcY",
  "version": "1",
  "versionID": "1-zV86jpeY"
}]
edition_metadata = [{
  "datasetID": "boligpriser_historic-4owcY",
  "description": "Manually uploaded file",
  "edition": 1551107009,
  "editionID": "EDITION-HAkZy",
  "endTime": "2017-12-31T23:00:00+01:00",
  "startTime": "2004-01-01T00:00:00+01:00",
  "versionID": "1-zV86jpeY"
}]

class Test:
    def test_main_handler(self, requests_mock, s3_client, s3_bucket):
        for i in range(0,19):
            s3_client.put_object(Bucket=s3_bucket, Key='{}{}.json'.format(urllib.parse.unquote_plus(base_key), f'{i:02}'), Body=json.dumps({'number': f'{i:02}'}))
        requests_mock.get('https://mvxwmcrn5m.execute-api.eu-west-1.amazonaws.com/dev/datasets/boligpriser_historic-4owcY/versions', text=json.dumps(version_metadata))
        requests_mock.get('https://mvxwmcrn5m.execute-api.eu-west-1.amazonaws.com/dev/datasets/boligpriser_historic-4owcY/versions/{}/editions'
                          .format(version_metadata[0]['versionID']), text=json.dumps(edition_metadata))

        key_to_get = main.latest_edition(event, {})
        print(key_to_get)
        assert 0

@fixture
def s3_client():
    with mock_s3():
        s3 = boto3.client('s3')
        yield s3

@fixture
def s3_bucket(s3_client):
    bucket = 'ok-origo-dataplatform-dev'
    s3_client.create_bucket(Bucket=bucket)
    return bucket

event = {
    "body": "eyJ0ZXN0IjoiYm9keSJ9",
    "resource": "/{dataset}",
    "path": "/",
    "httpMethod": "GET",
    "queryStringParameters": {
        "geography": ['02', '08', '12']
    },
    "pathParameters": {
        "dataset": "boligpriser_historic-4owcY"
    },
    "stageVariables": {
    },
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
        "X-Forwarded-Proto": "https"
    },
    "requestContext": {
        "accountId": "123456789012",
        "resourceId": "123456",
        "stage": "prod",
        "requestId": "c6af9ac6-7b61-11e6-9a41-93e8deadbeef",
        "requestTime": "09/Apr/2015:12:34:56 +0000",
        "requestTimeEpoch": 1428582896000,
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
            "user": None
        },
        "path": "/prod/path/to/resource",
        "resourcePath": "/{proxy+}",
        "httpMethod": "POST",
        "apiId": "1234567890",
        "protocol": "HTTP/1.1"
    }
}
