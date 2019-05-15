import json
import os
import re

import boto3
import requests

metadata_api = os.environ["METADATA_API_URL"]
bucket = "ok-origo-dataplatform-{}".format(os.environ["STAGE"])


def get_latest_edition(event, context):
    if event["requestContext"]["authorizer"]["principalId"] != "service-account-bydelsfakta-frontend":
        return {"statusCode": 403, "body": "Forbidden: Only bydelsfakta frontend is allowed to use this api"}

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

    all_versions = requests.get(f"{metadata_api}/datasets/{dataset}/versions")
    versions = json.loads(all_versions.text)
    latest_version = max(versions, key=lambda x: x["version"] if "version" in x else -1)
    version_name = latest_version.get("versionID", latest_version["version"])

    all_editions = requests.get(f"{metadata_api}/datasets/{dataset}/versions/{version_name}/editions")

    editions = json.loads(all_editions.text)
    latest_edition = max(editions, key=lambda x: x["edition"] if "edition" in x else -1)
    edition_name = latest_edition.get("editionID", latest_edition["edition"])

    base_key = f"processed/green/{dataset}/version={version_name}/edition={edition_name}/"

    data = gen_lists()

    return {"statusCode": 200, "headers": {"Content-Type": "application/json"}, "body": json.dumps(data, ensure_ascii=False)}


"""
/datasets/:id?geography=00,02,06,12

:id dataset id (path param)
geography query param for filter

"""
