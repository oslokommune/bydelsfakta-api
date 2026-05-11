import json
import logging

from service import S3FileNotFoundError, get_objects

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    dataset = event["pathParameters"]["dataset"]
    logger.info(f"Fetching Bydelsfakta data for {dataset}")

    if (
        not event["queryStringParameters"]
        or "geography" not in event["queryStringParameters"]
    ):
        return _response(400, "Missing required query parameter: geography")

    query = event["queryStringParameters"]["geography"]

    try:
        return _response(200, get_objects(dataset, query))
    except S3FileNotFoundError as e:
        return _response(404, str(e))


def _response(status, body):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, ensure_ascii=False),
    }
