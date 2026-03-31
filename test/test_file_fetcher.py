from unittest.mock import patch, MagicMock

import pytest

from doi_meta_retriever import FileFetcher, CoreData, ZenodoFileFetcher


@pytest.fixture
def demo_core_data():
    return CoreData(
        DOI='abc/def',
        title='ABC',
        publisher='Test',
        type='dataset',
        resolved_url='https://encoded.in.doi',
        actual_url='https://further.redirected.by.owner',
    )

@pytest.fixture
def files_request_mock():
    response_mock = MagicMock()
    response_mock.read.return_value = '''
    {
        "a": 42,
        "files": {
            "entries": {
                "test.csv": {
                    "key": "test.csv",
                    "size": 42,
                    "checksum": "sha1:ackakfdja",
                    "mimetype": "text/csv",
                    "troll": {
                        "value": "https://i.did.resolve"
                    },
                    "links": {
                        "content": "http://download.me.here"
                    }
                }
            }
        }
    }'''

    urlopen_mock = MagicMock()
    urlopen_mock.__enter__.return_value = response_mock

    return urlopen_mock

def test_file_fetcher_factory(demo_core_data):
    class TestFileFetcher(FileFetcher):
        ...

    fetcher = FileFetcher.factory(demo_core_data)
    assert isinstance(fetcher, TestFileFetcher)


def test_zenodo_file_fetcher(demo_core_data, files_request_mock):
    fetcher = ZenodoFileFetcher(demo_core_data)
    with patch('urllib.request.urlopen', return_value=files_request_mock) as mock_urlopen:
        file_list = fetcher.fetch()
        assert len(file_list) == 1
        assert file_list[0].url == 'http://download.me.here'
