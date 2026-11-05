"""Read the four CSVs directly from the supplied zip, after checking it is the expected file."""

from __future__ import annotations

import hashlib
import zipfile
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from lj import config

TABLES = {
    "ads": "ads.csv",
    "creators": "creators.csv",
    "posts": "creator_posts.csv",
    "audience": "creator_audience.csv",
}


class DataFileError(Exception):
    """The data zip is missing, altered, or incomplete."""


@dataclass
class RawData:
    ads: pd.DataFrame
    creators: pd.DataFrame
    posts: pd.DataFrame
    audience: pd.DataFrame


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_raw(path: Path | None = None, expected_sha256: str | None = config.EXPECTED_ZIP_SHA256) -> RawData:
    """Load all tables. Pass expected_sha256=None to skip the checksum (tests only)."""
    path = Path(path) if path else config.zip_path()
    if not path.exists():
        raise DataFileError(f"Data zip not found at {path}. Place it there or set LJ_DATA_ZIP.")
    if expected_sha256 is not None:
        actual = sha256_file(path)
        if actual != expected_sha256.lower():
            raise DataFileError(f"{path.name} checksum {actual} does not match the expected {expected_sha256}.")

    frames = {}
    with zipfile.ZipFile(path) as archive:
        names = {Path(name).name: name for name in archive.namelist()}
        for table, filename in TABLES.items():
            if filename not in names:
                raise DataFileError(f"{filename} is missing from {path.name}.")
            with archive.open(names[filename]) as handle:
                frames[table] = pd.read_csv(handle)
    return RawData(**frames)
