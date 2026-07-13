import pandas as pd
import pytest

from src.config import ITEM_KEY, JOIN_KEY, REQUIRED_NF_COLUMNS
from src.data_validation import (
    validate_dates,
    validate_required_columns,
    validate_unique_key,
)
from src.exceptions import CardinalityError, SchemaValidationError


def test_missing_required_column_identifies_source():
    frame = pd.DataFrame({"CD_EMPRESA": ["6"]})
    with pytest.raises(SchemaValidationError, match="NF: colunas obrigatórias ausentes"):
        validate_required_columns(frame, REQUIRED_NF_COLUMNS, "NF")


def test_duplicate_header_key_interrupts_processing(raw_sources):
    nf, _ = raw_sources
    duplicate = pd.concat([nf, nf.iloc[[0]]], ignore_index=True)
    with pytest.raises(CardinalityError, match="duplicidade"):
        validate_unique_key(duplicate, JOIN_KEY, "NF")


def test_invalid_official_date_is_diagnostic(raw_sources):
    nf, items = raw_sources
    invalid = nf.copy()
    invalid.loc[invalid.index[0], "DT_EMISSAO"] = pd.NaT
    with pytest.raises(SchemaValidationError, match="NF.DT_EMISSAO=1"):
        validate_dates(invalid, items)


def test_current_keys_are_complete_and_unique(raw_sources):
    nf, items = raw_sources
    assert not nf[JOIN_KEY].isna().any(axis=1).any()
    assert not items[ITEM_KEY].isna().any(axis=1).any()
    assert not nf.duplicated(JOIN_KEY).any()
    assert not items.duplicated(ITEM_KEY).any()
