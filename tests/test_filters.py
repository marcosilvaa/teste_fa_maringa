import pandas as pd
import pytest

from src.filters import FilterSpec, apply_filters
from src.metrics import compute_kpis


def test_no_filters_matches_regression(bundle):
    filtered = apply_filters(bundle, FilterSpec())
    assert compute_kpis(filtered.sales, filtered.returns)["faturamento_liquido"] == pytest.approx(7005896.50)


def test_date_filter_applies_to_sales_and_returns(bundle):
    target = pd.Timestamp("2026-03-02").date()
    filtered = apply_filters(bundle, FilterSpec(start_date=target, end_date=target))
    assert filtered.sales["DT_EMISSAO"].dt.date.eq(target).all()
    assert filtered.returns["DT_EMISSAO"].dt.date.eq(target).all()


def test_company_filters(bundle):
    selected = apply_filters(bundle, FilterSpec(billing_companies=("6",), source_companies=("6",)))
    assert len(selected.sales) == len(bundle.sales)
    empty = apply_filters(bundle, FilterSpec(billing_companies=("999",)))
    assert empty.sales.empty and empty.returns.empty


def test_product_and_unit_filters_preserve_scope(bundle):
    row = bundle.sales.iloc[0]
    filtered = apply_filters(
        bundle,
        FilterSpec(product_codes=(row["CD_PRODUTO"],), units=(row["CD_ESPECIE"],)),
    )
    assert filtered.sales["CD_PRODUTO"].eq(row["CD_PRODUTO"]).all()
    assert filtered.sales["CD_ESPECIE"].eq(row["CD_ESPECIE"]).all()
    assert filtered.returns["CD_PRODUTO"].eq(row["CD_PRODUTO"]).all()


def test_text_search_is_case_insensitive_and_literal(bundle):
    filtered = apply_filters(bundle, FilterSpec(description_query="colchao"))
    assert not filtered.sales.empty
    assert filtered.sales["DS_PRODUTO"].str.contains("colchao", case=False, regex=False).all()


def test_empty_result_is_safe(bundle):
    filtered = apply_filters(bundle, FilterSpec(description_query="produto inexistente 123xyz"))
    assert filtered.empty
    result = compute_kpis(filtered.sales, filtered.returns)
    assert result["faturamento_liquido"] == 0
