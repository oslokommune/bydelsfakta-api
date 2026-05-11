import json
import os

from app import lambda_handler

dataset_id = "boligpriser"
s3_prefix = os.environ["S3_PREFIX"]


def test_handler(s3_bucket, event):
    for i in range(0, 19):
        file_number = str(i).zfill(2)
        s3_bucket[0].put_object(
            Bucket=s3_bucket[1],
            Key=f"{s3_prefix}{dataset_id}/{file_number}.json",
            Body=json.dumps({"number": file_number}),
        )
    result = lambda_handler(event, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"])[1] == {"number": "08"}


def test_handler_missing_files(s3_bucket, event):
    result = lambda_handler(event, {})
    assert result["statusCode"] == 404


def test_handler_no_geography(s3_bucket, event):
    event["queryStringParameters"] = None
    result = lambda_handler(event, {})
    assert result["statusCode"] == 400
