import json
import os
import re

import boto3
import requests
import logging
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch

patch(["boto3"])
patch(["requests"])

metadata_api = os.environ["METADATA_API_URL"]
bucket = "ok-origo-dataplatform-{}".format(os.environ["STAGE"])

logger = logging.getLogger()
logger.setLevel(logging.INFO)

session = boto3.Session()
s3 = session.client("s3")


def handler(event, context):
    if (
        event["requestContext"]["authorizer"]["principalId"]
        != "service-account-bydelsfakta-frontend"
    ):
        return {
            "statusCode": 403,
            "body": "Forbidden: Only bydelsfakta frontend is allowed to use this api",
        }
    return handle_event(event)


@xray_recorder.capture("get_objects")
def gen_lists(base_key, query):
    logger.info(f"Fetching data from {base_key}")

    keys = []
    if not query:
        objects = s3.list_objects_v2(Bucket=bucket, Prefix=base_key)["Contents"]
        keys = [obj["Key"] for obj in objects]
    else:
        pattern = re.compile("(\d\d)")
        numbers = pattern.findall(query)
        keys = [f"{base_key}{geography}.json" for geography in numbers]

    if not keys:
        logger.info("No files where found for the dataset")
        return response(
            422,
            "Even though an edition exists, no files where found for the dataset",
        )

    return [
        json.loads(s3.get_object(Bucket=bucket, Key=key)["Body"].read().decode("utf-8"))
        for key in keys
    ]


@xray_recorder.capture("handle_event")
def handle_event(event):
    dataset_id = event["pathParameters"]["dataset"]
    logger.info(f"Fetching Bydelsfakta data for {dataset_id}")

    dataset_response = requests.get(f"{metadata_api}/datasets/{dataset_id}")
    if dataset_response.status_code == 404:
        return response(404, f"No dataset with id {dataset_id}")

    dataset = json.loads(dataset_response.text)
    stage = dataset["processing_stage"]
    confidentiality = dataset["confidentiality"]
    parent_id = dataset.get("parent_id", None)

    if not parent_id:
        logger.info(f"{dataset_id} is missing parent_id")
        return response(
            422,
            "Was expecting to find a parent_id on the requested resource but was None",
        )

    query = []
    if event["queryStringParameters"] and "geography" in event["queryStringParameters"]:
        query = event["queryStringParameters"]["geography"]

    try:
        version = get_latest_version(dataset_id)
    except IllegalFormatError:
        return response(400, "One or more versions have illegal format")

    try:
        edition = get_latest_edition(dataset_id, version)
    except IllegalFormatError:
        return response(400, "One or more editions have illegal format")

    edition_id = edition["Id"].split("/")[-1]

    base_key = f"{stage}/{confidentiality}/{parent_id}/{dataset_id}/version={version}/edition={edition_id}/"
    data = gen_lists(base_key, query)

    return response(200, data)


@xray_recorder.capture("get_version")
def get_latest_version(dataset_id):
    all_versions = requests.get(f"{metadata_api}/datasets/{dataset_id}/versions")
    all_versions = json.loads(all_versions.text)
    if not all(["Id" in version for version in all_versions]):
        logger.info("Versions with bad format was found:")
        logger.info([version for version in all_versions if "Id" not in version])
        raise IllegalFormatError("Wrong format")
    latest_version = max(
        all_versions, key=lambda x: x["version"] if "version" in x else -1
    )
    return latest_version["version"]


@xray_recorder.capture("get_edition")
def get_latest_edition(dataset_id, version):
    all_editions = requests.get(
        f"{metadata_api}/datasets/{dataset_id}/versions/{version}/editions"
    )
    all_editions = json.loads(all_editions.text)
    if not all(["Id" in edition for edition in all_editions]):
        logger.info("Editions with bad format was found:")
        logger.info([edition for edition in all_editions if "Id" not in edition])
        raise IllegalFormatError("Wrong format")
    return max(all_editions, key=lambda x: x["Id"] if "Id" in x else -1)


def response(status, body):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, ensure_ascii=False),
    }


class IllegalFormatError(Exception):
    pass
