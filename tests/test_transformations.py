import pandas as pd
import pytest

from src.config import ITEM_KEY, SALES_OPERATIONS
from src.exceptions import CardinalityError
from src.transformations import prepare_analytical_data


def test_filter_effective_headers_and_merge_many_to_one(bundle):
    assert len(bundle.valid_nf) == 34466
    assert len(bundle.integrated) == 48248
    assert len(bundle.unmatched_items) == 1366


def test_sales_returns_and_exclusions_are_classified(bundle):
    assert set(bundle.sales["CFOP_TIPO_OPERACAO"].unique()) == set(SALES_OPERATIONS)
    assert set(bundle.returns["CFOP_TIPO_OPERACAO"].unique()) == {"DEVOLUCAO"}
    assert bundle.returns["CFOP_TIPO_FLUXO"].eq("ENTRADA").all()
    assert bundle.returns["TIPO_ITEM_FISCAL"].eq("PRODUTO").all()
    assert not bundle.excluded["CFOP_TIPO_OPERACAO"].isin(SALES_OPERATIONS).any()
    assert "TRANSFERENCIA" in set(bundle.excluded["CFOP_TIPO_OPERACAO"])
    assert "AQUISICAO SERVICO TRANSPORTE" in set(bundle.excluded["CFOP_TIPO_OPERACAO"])


def test_official_date_comes_from_header(bundle):
    assert "DT_EMISSAO" in bundle.integrated
    assert bundle.integrated["DT_EMISSAO"].min() == pd.Timestamp("2026-03-01")
    assert bundle.integrated["DT_EMISSAO"].max() == pd.Timestamp("2026-03-31")


def test_current_dataset_has_no_flow_inconsistency(bundle):
    assert bundle.flow_issues.empty


def test_flow_inconsistency_is_exposed(raw_sources, bundle):
    nf, items = raw_sources
    changed = items.copy()
    row = bundle.integrated.iloc[0]
    mask = changed[ITEM_KEY].eq(row[ITEM_KEY]).all(axis=1)
    changed.loc[mask, "CFOP_TIPO_FLUXO"] = "ENTRADA" if row["CFOP_TIPO_FLUXO"] == "SAIDA" else "SAIDA"
    result = prepare_analytical_data(nf, changed)
    assert len(result.flow_issues) == 1


def test_duplicate_header_key_fails_before_merge(raw_sources):
    nf, items = raw_sources
    duplicate = pd.concat([nf, nf.iloc[[0]]], ignore_index=True)
    with pytest.raises(CardinalityError):
        prepare_analytical_data(duplicate, items)
