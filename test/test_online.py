from doi_meta_retriever import resolve_core_data, FileFetcher


def test_online():
    core_data = resolve_core_data('10.5281/zenodo.17831177')
    fetcher = FileFetcher.factory(core_data)
    files = fetcher.fetch()

    assert len(files) == 7
    assert files[5].checksum == 'md5:ceea01454d3b03990a19324596228a33'
