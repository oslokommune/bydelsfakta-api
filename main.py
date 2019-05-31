import json
import os
import re

import boto3
import requests
import logging

metadata_api = os.environ["METADATA_API_URL"]
bucket = "ok-origo-dataplatform-{}".format(os.environ["STAGE"])

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    if event["requestContext"]["authorizer"]["principalId"] != "service-account-bydelsfakta-frontend":
        return {"statusCode": 403, "body": "Forbidden: Only bydelsfakta frontend is allowed to use this api"}
    return handle_event(event)


def handle_event(event):
    def gen_lists():
        keys = []
        if not query:
            objects = s3.list_objects_v2(Bucket=bucket, Prefix=base_key)["Contents"]
            keys = [obj["Key"] for obj in objects]
        else:
            pattern = re.compile("(\d\d)")
            numbers = pattern.findall(query)
            keys = [f"{base_key}{geography}.json" for geography in numbers]

        return [json.loads(s3.get_object(Bucket=bucket, Key=key)["Body"].read().decode("utf-8")) for key in keys]

    session = boto3.Session()
    s3 = session.client("s3")

    dataset = event["pathParameters"]["dataset"]
    query = []
    if event["queryStringParameters"] and "geography" in event["queryStringParameters"]:
        query = event["queryStringParameters"]["geography"]

    try:
        version = get_latest_version(dataset)
    except IllegalFormatError:
        return response(400, "One or more versions have illegal format")

    try:
        edition = get_latest_edition(dataset, version)
    except IllegalFormatError:
        return response(400, "One or more editions have illegal format")

    edition_id = edition["Id"].split("/")[-1]

    base_key = f"processed/green/{dataset}/version={version}/edition={edition_id}/"
    data = gen_lists()

    return {"statusCode": 200, "headers": {"Content-Type": "application/json"}, "body": json.dumps(data, ensure_ascii=False)}


def get_latest_version(dataset_id):
    all_versions = requests.get(f"{metadata_api}/datasets/{dataset_id}/versions")
    all_versions = json.loads(all_versions.text)
    if not all(["Id" in version for version in all_versions]):
        logger.info("Versions with bad format was found:")
        logger.info([edition for edition in all_versions if "Id" not in edition])
        raise IllegalFormatError("Wrong format")
    latest_version = max(all_versions, key=lambda x: x["version"] if "version" in x else -1)
    return latest_version["version"]


def get_latest_edition(dataset_id, version):
    all_editions = requests.get(f"{metadata_api}/datasets/{dataset_id}/versions/{version}/editions")
    all_editions = json.loads(all_editions.text)
    if not all(["Id" in edition for edition in all_editions]):
        logger.info("Editions with bad format was found:")
        logger.info([edition for edition in all_editions if "Id" not in edition])
        raise IllegalFormatError("Wrong format")
    return max(all_editions, key=lambda x: x["edition"] if "edition" in x else -1)


def response(status, body):
    return {"statusCode": status, "headers": {"Content-Type": "application/json"}, "body": json.dumps(body, ensure_ascii=False)}


class IllegalFormatError(Exception):
    pass
