import json
import logging
import os

import requests
from aws_xray_sdk.core import patch, xray_recorder

from bydelsfakta_api.service import get_latest_edition, get_latest_version, get_objects
from bydelsfakta_api.exceptions import IllegalFormatError, S3FileNotFoundError

patch(["requests"])

metadata_api = os.environ["METADATA_API_URL"]


logger = logging.getLogger()
logger.setLevel(logging.INFO)

CONFIDENTIALITY_MAP = {
    "public": "green",
    "restricted": "yellow",
    "non-public": "red",
}


def handler(event, context):
    if (
        event["requestContext"]["authorizer"]["principalId"]
        != "service-account-bydelsfakta-frontend"
    ):
        return {
            "statusCode": 403,
            "body": "Forbidden: Only the Bydelsfakta frontend is allowed to use this API",
        }
    return _handle_event(event)


@xray_recorder.capture("handle_event")
def _handle_event(event):
    dataset_id = event["pathParameters"]["dataset"]
    logger.info(f"Fetching Bydelsfakta data for {dataset_id}")

    dataset_response = requests.get(f"{metadata_api}/datasets/{dataset_id}")
    if dataset_response.status_code == 404:
        return _response(404, f"No dataset with id {dataset_id}")

    dataset = json.loads(dataset_response.text)
    stage = dataset.get("processing_stage", "processed")
    confidentiality = (
        CONFIDENTIALITY_MAP[dataset["accessRights"]]
        if "accessRights" in dataset
        else dataset["confidentiality"]
    )
    parent_id = dataset.get("parent_id", None)

    query = []
    if event["queryStringParameters"] and "geography" in event["queryStringParameters"]:
        query = event["queryStringParameters"]["geography"]

    try:
        version = get_latest_version(dataset_id)
    except IllegalFormatError:
        return _response(400, "One or more versions have illegal format")

    try:
        edition = get_latest_edition(dataset_id, version)
    except IllegalFormatError:
        return _response(400, "One or more editions have illegal format")

    edition_id = edition["Id"].split("/")[-1]

    base_key = "/".join(
        [
            stage,
            confidentiality,
            *([parent_id] if parent_id else []),
            dataset_id,
            f"version={version}",
            f"edition={edition_id}",
            "",
        ]
    )

    try:
        return _response(200, get_objects(base_key, query))
    except S3FileNotFoundError as e:
        return _response(422, str(e))


def _response(status, body):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, ensure_ascii=False),
    }
