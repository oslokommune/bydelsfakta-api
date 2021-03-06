import json
import os
import urllib

import boto3
import pytest
from moto import mock_s3
from pytest import fixture

stage = "test"
m_url = "https://metadata.com/{}".format(stage)
os.environ["METADATA_API_URL"] = m_url
os.environ["STAGE"] = stage
import main  # noqa: E402

parent_id = "bydelsfakta"
dataset_id = "boligpriser"
version = 1

dataset_metadata = {
    "Id": dataset_id,
    "processing_stage": "raw",
    "confidentiality": "green",
    "parent_id": parent_id,
}
version_metadata = [{"Id": f"{dataset_id}/{version}", "version": f"{version}"}]
version_metadata_old = [{"versionID": f"{dataset_id}/{version}"}]
edition_metadata = [
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

edition_metadata_old = [
    {
        "editionID": "EDITION-20190529T113052",
        "description": "Latest Edition",
        "edition": "2019-05-29T13:30:52+02:00",
        "endTime": "2017-12-31T23:00:00+01:00",
        "startTime": "2004-01-01T00:00:00+01:00",
    }
]


class Test:
    base_key = (
        f"raw/green/{parent_id}/{dataset_id}/version%3D1/edition%3D20190529T113052/"
    )

    def test_main_handler(self, requests_mock, s3_bucket):
        for i in range(0, 19):
            prefix = urllib.parse.unquote_plus(self.base_key)
            file_numer = str(i).zfill(2)
            print(f"{prefix}{file_numer}.json")
            s3_bucket[0].put_object(
                Bucket=s3_bucket[1],
                Key=f"{prefix}{file_numer}.json",
                Body=json.dumps({"number": file_numer}),
            )
        requests_mock.get(
            f"{m_url}/datasets/{dataset_id}", text=json.dumps(dataset_metadata)
        )
        requests_mock.get(
            f"{m_url}/datasets/{dataset_id}/versions",
            text=json.dumps(version_metadata),
        )
        requests_mock.get(
            f"{m_url}/datasets/{dataset_id}/versions/{version_metadata[0]['version']}/editions",
            text=json.dumps(edition_metadata),
        )
        result = main.handler(event, {})
        assert result["statusCode"] == 200
        assert json.loads(result["body"])[1] == {"number": "08"}

    def test_main_handler_missing_files(self, requests_mock, s3_bucket):
        requests_mock.get(
            f"{m_url}/datasets/{dataset_id}", text=json.dumps(dataset_metadata)
        )
        requests_mock.get(
            f"{m_url}/datasets/{dataset_id}/versions",
            text=json.dumps(version_metadata),
        )
        requests_mock.get(
            f"{m_url}/datasets/{dataset_id}/versions/{version_metadata[0]['version']}/editions",
            text=json.dumps(edition_metadata),
        )
        result = main.handler(event, {})
        assert result["statusCode"] == 422
        base_key = urllib.parse.unquote_plus(self.base_key)
        assert (
            json.loads(result["body"]) == f"File {base_key}02.json could not be found"
        )

    def test_main_handler_on_non_existing_dataset(self, requests_mock):
        requests_mock.get(f"{m_url}/datasets/{dataset_id}", status_code=404)
        result = main.handler(event, {})
        assert result["statusCode"] == 404
        assert json.loads(result["body"]) == f"No dataset with id {dataset_id}"

    def test_get_latest_version(self, requests_mock):
        versions = version_metadata + [{"Id": f"{dataset_id}/2", "version": "2"}]
        requests_mock.get(
            f"{m_url}/datasets/{dataset_id}/versions", text=json.dumps(versions)
        )
        assert main.get_latest_version(dataset_id) == "2"

    def test_fail_on_old_version(self, requests_mock):
        requests_mock.get(
            m_url + f"/datasets/{dataset_id}/versions",
            text=json.dumps(version_metadata_old),
        )
        with pytest.raises(main.IllegalFormatError):
            main.get_latest_version(dataset_id)

    def test_get_latest_edition(self, requests_mock):
        requests_mock.get(
            f"{m_url}/datasets/{dataset_id}/versions/1/editions",
            text=json.dumps(edition_metadata),
        )
        assert main.get_latest_edition(dataset_id, version=1) == edition_metadata[0]

    def test_fail_on_old_edition(self, requests_mock):
        requests_mock.get(
            f"{m_url}/datasets/{dataset_id}/versions/1/editions",
            text=json.dumps(edition_metadata_old),
        )
        with pytest.raises(main.IllegalFormatError):
            main.get_latest_edition(dataset_id, version=1)


@fixture
def s3_client():
    with mock_s3():
        s3 = boto3.client("s3")
        yield s3


@fixture
def s3_bucket(s3_client):
    bucket = "ok-origo-dataplatform-test"
    s3_client.create_bucket(Bucket=bucket)
    return s3_client, bucket


event = {
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
