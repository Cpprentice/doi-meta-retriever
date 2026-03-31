import io
from unittest.mock import patch, MagicMock

import pytest

from doi_meta_retriever import get_doi_and_doi_url, CoreData, FileRecord, find, resolve_core_data, resolve_url_from_doi


def test_get_doi_and_doi_url():
    doi_url_prefix = 'https://doi.org/'

    doi = 'abc/def'
    assert get_doi_and_doi_url(doi) == (doi, f'{doi_url_prefix}abc/def')

    doi = '241.0/23291aca'
    assert get_doi_and_doi_url(f'{doi_url_prefix}{doi}') == (doi, f'{doi_url_prefix}{doi}')


def test_core_data_from_response_dict():

    with pytest.raises(TypeError):
        core_data = CoreData.from_response_dict({
            'DOI': 'abc/def',
            'title': 'ABC',
            'troll': 'whatever'
        })

    core_data = CoreData.from_response_dict({
        'DOI': 'abc/def',
        'title': 'ABC',
        'troll': 'whatever',
        'resolved_url': 'https://encoded.in.doi',
        'actual_url': 'https://further.redirected.by.owner',
        'publisher': 'Zenodo',
        'type': 'dataset'
    })
    assert core_data.DOI == 'abc/def'
    assert core_data.title == 'ABC'
    assert core_data.resolved_url == 'https://encoded.in.doi'
    assert core_data.actual_url == 'https://further.redirected.by.owner'
    assert core_data.publisher == 'Zenodo'
    assert core_data.type == 'dataset'

def test_file_record_from_response_dict():
    with pytest.raises(TypeError):
        file_record = FileRecord.from_response_dict({
            'key': 'filename.csv',
            'url': 'https://download.me.here',
            'troll': 'whatever'
        })

    file_record = FileRecord.from_response_dict({
        'key': 'filename.csv',
        'url': 'https://download.me.here',
        'troll': 'whatever',
        'size': 42,
        'checksum': 'md5:blubblub',
        'mimetype': 'text/csv'
    })

    assert file_record.key == 'filename.csv'
    assert file_record.url == 'https://download.me.here'
    assert file_record.size == 42
    assert file_record.checksum == 'md5:blubblub'
    assert file_record.mimetype == 'text/csv'


def test_find():
    values = [10, 20, 30, 40, 50]
    first_value_larger_25 = find(values, lambda v: v > 25)
    assert first_value_larger_25 == 30
    assert find(values, lambda v: v > 125) is None


@pytest.fixture
def request_mock():
    response_mock = MagicMock()
    response_mock.geturl.return_value = 'http://example.com'
    response_mock.read.return_value = b'{"a": 42, "values": [{"type": "URL", "data": {"value": "https://i.did.resolve"}}]}'

    urlopen_mock = MagicMock()
    urlopen_mock.__enter__.return_value = response_mock

    return urlopen_mock

@pytest.fixture
def request_with_loc_mock():
    response_mock = MagicMock()
    response_mock.geturl.return_value = 'http://example.com'
    response_mock.read.return_value = '''{
    "a": 42,
    "values": [
        {
             "type": "10320/loc",
             "data": {
                "value": "<main><entry href=\\"http://link.in.xml\\"/></main>"
             }
        }
    ]
}'''

    urlopen_mock = MagicMock()
    urlopen_mock.__enter__.return_value = response_mock

    return urlopen_mock

@pytest.fixture
def demo_core_data():
    return CoreData(
        DOI='abc/def',
        title='ABC',
        publisher='Zenodo',
        type='dataset',
        resolved_url='https://encoded.in.doi',
        actual_url='https://further.redirected.by.owner',
    )

def test_resolve_core_data(request_mock, request_with_loc_mock, demo_core_data):
    doi = 'abc/def'
    with patch('doi_meta_retriever.CoreData.from_response_dict', return_value=demo_core_data):
        with patch('urllib.request.urlopen', return_value=request_mock) as mock_urlopen:
            core_data = resolve_core_data(doi)
            assert core_data.resolved_url == 'https://encoded.in.doi'
        with patch('urllib.request.urlopen', return_value=request_with_loc_mock) as mock_urlopen:
            core_data = resolve_core_data(doi)


def test_resolve_url_from_doi(request_with_loc_mock):
    doi = 'abc/def'
    with patch('urllib.request.urlopen', return_value=request_with_loc_mock) as mock_urlopen:
        url = resolve_url_from_doi(doi)
        assert url == 'http://link.in.xml'