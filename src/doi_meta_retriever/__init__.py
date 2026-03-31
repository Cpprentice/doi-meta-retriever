import functools
import inspect
import json
import re
from dataclasses import dataclass
import urllib.request
from typing import Any, Self, Collection, Callable
import xml.etree.ElementTree as ET


@dataclass
class CoreData:
    DOI: str
    resolved_url: str
    actual_url: str
    title: str
    publisher: str
    type: str

    @classmethod
    def from_response_dict(cls, data: dict[str, Any]) -> Self:
        return cls(**{
            k: v
            for k, v in data.items()
            if k in inspect.signature(cls).parameters
        })


@dataclass
class FileRecord:
    key: str
    url: str
    size: int
    checksum: str
    mimetype: str

    @classmethod
    def from_response_dict(cls, data: dict[str, Any]) -> Self:
        return cls(**{
            k: v
            for k, v in data.items()
            if k in inspect.signature(cls).parameters
        })


def get_doi_and_doi_url(doi_or_doi_url: str) -> tuple[str, str]:
    doi = re.sub(r'^https?://doi.org/', r'', doi_or_doi_url, flags=re.IGNORECASE)
    doi_url = f'https://doi.org/{doi}'
    return doi, doi_url



def resolve_core_data(doi_or_doi_url: str) -> CoreData:
    doi, doi_url = get_doi_and_doi_url(doi_or_doi_url)
    request = urllib.request.Request(doi_url, headers={'Accept': 'application/vnd.citationstyles.csl+json'})
    with urllib.request.urlopen(request) as response:
        data = json.load(response)
        # response.geturl() here returns the crosscite endpoints used to deliver the citationstyles response
    data['actual_url'] = resolve_actual_url(doi_url)
    data['resolved_url'] = resolve_url_from_doi(doi)
    return CoreData.from_response_dict(data)


def find(container: Collection, predicate: Callable[[Any], bool]) -> Any | None:
    return functools.reduce(
        lambda acc, val: acc if acc is not None else (val if predicate(val) else None),
        container,
        None
    )


def resolve_actual_url(doi_url: str) -> str:
    with urllib.request.urlopen(doi_url) as response:
        return response.geturl()


def resolve_url_from_doi(doi: str) -> str:
    with urllib.request.urlopen(f'https://doi.org/api/handles/{doi}') as response:
        data = json.load(response)

    # Inspired by https://github.com/lcnittl/pyDOI
    url_entry = find(data['values'], lambda x: x['type'] == 'URL')
    if url_entry is not None:
        return url_entry['data']['value']
    # TODO look for URL that actually contains this
    loc_entry = find(data['values'], lambda x: x['type'] == '10320/loc')
    if loc_entry is not None:
        xml = ET.fromstring(loc_entry['data']['value'])
        nodes = xml.findall(".//*[@href]")
        return nodes[0].attrib['href']
    raise RuntimeError('Could not resolve DOI to actual URL')


class FileFetcher:
    _registry: dict[str, type[Self]] = {}

    def __init__(self, core_data: CoreData, *args, **kwargs):
        self.core_data = core_data

    def __init_subclass__(cls, **kwargs):
        cls._registry[cls.__name__[:-11]] = cls
        super().__init_subclass__()

    @classmethod
    def factory(cls, core_data: CoreData, *args, **kwargs) -> Self:
        class_ = cls._registry[core_data.publisher]
        return class_(core_data, *args, **kwargs)

    def fetch(self) -> list[FileRecord]:
        # Intended for overriding
        ...


class ZenodoFileFetcher(FileFetcher):
    def fetch(self) -> list[FileRecord]:
        with urllib.request.urlopen(f'{self.core_data.actual_url}/export/json') as response:
            data = json.load(response)
        files = []
        for entry in data['files']['entries'].values():
            entry['url'] = entry['links']['content']
            files.append(FileRecord.from_response_dict(entry))
        _ = 42
        return files
