import json
import os

import pytest

from bydelsfakta_api.exceptions import IllegalFormatError
from bydelsfakta_api.service import get_latest_edition, get_latest_version

metadata_api_url = os.environ["METADATA_API_URL"]
dataset_id = "boligpriser"


def test_get_latest_version_success(requests_mock, version_metadata):
    versions = version_metadata + [{"Id": f"{dataset_id}/2", "version": "2"}]
    requests_mock.get(
        f"{metadata_api_url}/datasets/{dataset_id}/versions",
        text=json.dumps(versions),
    )
    assert get_latest_version(dataset_id) == "2"


def test_get_latest_version_fail_on_old_version(requests_mock, version_metadata_old):
    requests_mock.get(
        metadata_api_url + f"/datasets/{dataset_id}/versions",
        text=json.dumps(version_metadata_old),
    )
    with pytest.raises(IllegalFormatError):
        get_latest_version(dataset_id)


def test_get_latest_edition_success(requests_mock, edition_metadata):
    requests_mock.get(
        f"{metadata_api_url}/datasets/{dataset_id}/versions/1/editions",
        text=json.dumps(edition_metadata),
    )
    assert get_latest_edition(dataset_id, version=1) == edition_metadata[0]


def test_get_latest_edition_fail_on_old_edition(requests_mock):
    requests_mock.get(
        f"{metadata_api_url}/datasets/{dataset_id}/versions/1/editions",
        text=json.dumps(
            [
                {
                    "editionID": "EDITION-20190529T113052",
                    "description": "Latest Edition",
                    "edition": "2019-05-29T13:30:52+02:00",
                    "endTime": "2017-12-31T23:00:00+01:00",
                    "startTime": "2004-01-01T00:00:00+01:00",
                }
            ]
        ),
    )
    with pytest.raises(IllegalFormatError):
        get_latest_edition(dataset_id, version=1)
