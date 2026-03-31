# DOI-Meta-Retriever

This package lets you download information on files that are behind a DOI.

For now, the implementation is limited to Zenodo, but it can easily be extended by creating more FileFetcher 
classes that know about the API of other publishers.

## Usage

```python

from doi_meta_retriever import resolve_core_data, FileFetcher


core_data = resolve_core_data('your/doi/of/interest')
fetcher = FileFetcher.factory(core_data)
files = fetcher.fetch()

```

The data is returned as dataclass instances respectively providing the following attributes each:

```python
class CoreData:
    DOI: str
    resolved_url: str
    actual_url: str
    title: str
    publisher: str
    type: str
```

Note that there is a difference between the URL that the DOI is resolving to and what the respective target platform might do
in further resolutions.
For Zenodo this means that `resolved_url` and `actual_url` will have different values.




```python
class FileRecord:
    key: str
    url: str
    size: int
    checksum: str
    mimetype: str
```


Example records:
```json
{
  "DOI" : "10.5281/ZENODO.17831177",
  "resolved_url" : "https://zenodo.org/doi/10.5281/zenodo.17831177",
  "actual_url" : "https://zenodo.org/records/17831177",
  "title" : "Real-world energy data of 200 feeders from low-voltage grids with metadata in Germany over two years",
  "publisher" : "Zenodo",
  "type" : "dataset"
}
```

```json
{
    "key": "feeder_metadata.csv",
    "url": "https://zenodo.org/api/records/17831177/files/feeder_metadata.csv",
    "size": 171296,
    "checksum": "md5:ceea01454d3b03990a19324596228a33",
    "mimetype": "text/csv"
}
```