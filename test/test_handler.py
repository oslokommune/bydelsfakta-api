import json
import os

from bydelsfakta_api.handler import handler

metadata_api_url = os.environ["METADATA_API_URL"]
dataset_id = "boligpriser"


def test_handler(
    requests_mock,
    s3_bucket,
    event,
    dataset_metadata,
    version_metadata,
    edition_metadata,
    s3_prefix,
):
    for i in range(0, 19):
        file_numer = str(i).zfill(2)
        print(f"{s3_prefix}{file_numer}.json")
        s3_bucket[0].put_object(
            Bucket=s3_bucket[1],
            Key=f"{s3_prefix}{file_numer}.json",
            Body=json.dumps({"number": file_numer}),
        )
    requests_mock.get(
        f"{metadata_api_url}/datasets/{dataset_id}",
        text=json.dumps(dataset_metadata),
    )
    requests_mock.get(
        f"{metadata_api_url}/datasets/{dataset_id}/versions",
        text=json.dumps(version_metadata),
    )
    requests_mock.get(
        f"{metadata_api_url}/datasets/{dataset_id}/versions/{version_metadata[0]['version']}/editions",
        text=json.dumps(edition_metadata),
    )
    result = handler(event, {})
    assert result["statusCode"] == 200
    assert json.loads(result["body"])[1] == {"number": "08"}


def test_handler_missing_files(
    requests_mock,
    s3_bucket,
    event,
    dataset_metadata,
    version_metadata,
    edition_metadata,
    s3_prefix,
):
    requests_mock.get(
        f"{metadata_api_url}/datasets/{dataset_id}",
        text=json.dumps(dataset_metadata),
    )
    requests_mock.get(
        f"{metadata_api_url}/datasets/{dataset_id}/versions",
        text=json.dumps(version_metadata),
    )
    requests_mock.get(
        f"{metadata_api_url}/datasets/{dataset_id}/versions/{version_metadata[0]['version']}/editions",
        text=json.dumps(edition_metadata),
    )
    result = handler(event, {})
    assert result["statusCode"] == 422
    assert json.loads(result["body"]) == f"File {s3_prefix}02.json could not be found"


def test_handler_on_non_existing_dataset(requests_mock, event):
    requests_mock.get(f"{metadata_api_url}/datasets/{dataset_id}", status_code=404)
    result = handler(event, {})
    assert result["statusCode"] == 404
    assert json.loads(result["body"]) == f"No dataset with id {dataset_id}"
