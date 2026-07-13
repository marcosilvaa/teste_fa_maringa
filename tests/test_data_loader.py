from pathlib import Path

import pytest

from src.data_loader import load_sources, source_signature
from src.exceptions import DataSourceError


def test_missing_source_has_diagnostic_message(tmp_path: Path):
    missing = tmp_path / "NF.csv"
    with pytest.raises(DataSourceError, match="Arquivo obrigatório não encontrado"):
        source_signature(missing)


def test_source_signature_changes_with_file_content(tmp_path: Path):
    source = tmp_path / "source.csv"
    source.write_text("a\n1\n", encoding="utf-8")
    first = source_signature(source)
    source.write_text("a\n1\n2\n", encoding="utf-8")
    second = source_signature(source)
    assert first != second


def test_fiscal_codes_preserve_leading_zeros(raw_sources):
    _, items = raw_sources
    tipi = items["CD_TIPI"].dropna()
    assert tipi.str.len().min() == 8
    assert "00000000" in set(tipi)


def test_load_sources_returns_expected_current_shapes(raw_sources):
    nf, items = raw_sources
    assert nf.shape == (35414, 35)
    assert items.shape == (49614, 47)
