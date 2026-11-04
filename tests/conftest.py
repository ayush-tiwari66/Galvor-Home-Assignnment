import pytest

from lj import clean, config, ingest


@pytest.fixture(scope="session")
def raw():
    """The supplied data. Tests that need it skip when the zip is absent, since it isn't in the repo."""
    if not config.zip_path().exists():
        pytest.skip("little-joys-data.zip not available")
    return ingest.load_raw()


@pytest.fixture(scope="session")
def data(raw):
    return clean.clean_all(raw)
