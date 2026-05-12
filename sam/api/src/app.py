import json

from service import S3FileNotFoundError, get_objects


def lambda_handler(event, context):
    dataset = event["pathParameters"]["dataset"]

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
