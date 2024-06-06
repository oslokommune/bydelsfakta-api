import json
import logging
import os
import re

import boto3
import botocore
import requests
from aws_xray_sdk.core import patch, xray_recorder

from bydelsfakta_api.exceptions import IllegalFormatError, S3FileNotFoundError

patch(["boto3"])
patch(["requests"])

metadata_api = os.environ["METADATA_API_URL"]

logger = logging.getLogger()
logger.setLevel(logging.INFO)

session = boto3.Session()
s3 = session.client("s3")

bucket = "ok-origo-dataplatform-{}".format(os.environ["STAGE"])


@xray_recorder.capture("get_objects")
def get_objects(base_key, query):
    logger.info(f"Fetching data from {base_key}")

    if not query:
        objs = s3.list_objects_v2(Bucket=bucket, Prefix=base_key)["Contents"]
        keys = [obj["Key"] for obj in objs]
    else:
        pattern = re.compile(r"(\d\d)")
        numbers = pattern.findall(query)
        keys = [f"{base_key}{geography}.json" for geography in numbers]

    if not keys:
        raise S3FileNotFoundError(
            "Even though an edition exists, no files were found for the dataset"
        )

    objects = []
    for key in keys:
        try:
            obj = s3.get_object(Bucket=bucket, Key=key)["Body"].read().decode("utf-8")
        except botocore.exceptions.ClientError as e:
            if e.response.get("Error", {}).get("Code") == "NoSuchKey":
                raise S3FileNotFoundError(f"File {key} could not be found")
            raise
        objects.append(json.loads(obj))

    return objects


@xray_recorder.capture("get_latest_version")
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


@xray_recorder.capture("get_latest_edition")
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
