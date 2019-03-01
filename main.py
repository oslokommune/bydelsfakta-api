import os
import re

import requests
import json
import boto3

metadata_api = os.environ["METADATA_API_URL"]
bucket = "ok-origo-dataplatform-{}".format(os.environ["STAGE"])


def latest_edition(event, context):
    if (
        not event["requestContext"]["authorizer"]["principalId"]
        == "service-account-bydelsfakta-frontend"
    ):
        return {
            "statusCode": 403,
            "body": "Forbidden: Only bydelsfakta frontend is allowed to use this api",
        }

    def gen_lists():
        if not query:
            keys = [
                obj["Key"]
                for obj in s3.list_objects_v2(Bucket=bucket, Prefix=base_key)[
                    "Contents"
                ]
            ]
        else:
            pattern = re.compile("(\d\d)")
            numbers = pattern.findall(query)
            keys = ["{}{}.json".format(base_key, geography) for geography in numbers]

        return [
            json.loads(
                s3.get_object(Bucket=bucket, Key=key)["Body"].read().decode("utf-8")
            )
            for key in keys
        ]

    session = boto3.Session()
    s3 = session.client("s3")

    dataset = event["pathParameters"]["dataset"]
    query = []
    if event["queryStringParameters"] and "geography" in event["queryStringParameters"]:
        query = event["queryStringParameters"]["geography"]

    all_versions = requests.get(
        "{}/{}/{}/versions".format(metadata_api, "datasets", dataset)
    )
    versions = json.loads(all_versions.text)
    latest_version = max(versions, key=lambda x: x["version"] if "version" in x else -1)

    all_editions = requests.get(
        "{}/{}/{}/versions/{}/editions".format(
            metadata_api, "datasets", dataset, latest_version["versionID"]
        )
    )
    editions = json.loads(all_editions.text)
    latest_edition = max(editions, key=lambda x: x["edition"] if "edition" in x else -1)

    base_key = "processed/green/{}/version={}/edition={}/".format(
        dataset, latest_version["versionID"], latest_edition["editionID"]
    )

    data = gen_lists()

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(data, ensure_ascii=False),
    }


"""
/datasets/:id?geography=00,02,06,12

:id dataset id (path param)
geography query param for filter

"""
