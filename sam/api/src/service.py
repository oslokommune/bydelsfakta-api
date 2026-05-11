import json
import logging
import os
import re

import boto3
import botocore

logger = logging.getLogger()
logger.setLevel(logging.INFO)

session = boto3.Session()
s3 = session.client("s3")

bucket = os.environ["S3_BUCKET"]
prefix = os.environ["S3_PREFIX"]


class S3FileNotFoundError(Exception):
    pass


def get_objects(dataset, query):
    base_key = f"{prefix}{dataset}/"
    logger.info(f"Fetching data from {base_key}")

    pattern = re.compile(r"(\d\d)")
    numbers = pattern.findall(query)
    keys = [f"{base_key}{geography}.json" for geography in numbers]

    if not keys:
        raise S3FileNotFoundError("No files were found for the dataset")

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
