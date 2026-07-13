from pathlib import Path

import pytest

from src.data_loader import load_sources
from src.transformations import prepare_analytical_data


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def raw_sources():
    return load_sources(ROOT / "data" / "NF.csv", ROOT / "data" / "NFITEM.csv")


@pytest.fixture(scope="session")
def bundle(raw_sources):
    nf, items = raw_sources
    return prepare_analytical_data(nf, items)
