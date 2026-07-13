import pandas as pd
import pytest

from src.metrics import (
    aggregate_companies,
    aggregate_products,
    aggregate_temporal,
    compute_kpis,
)


EXPECTED = {
    "faturamento_bruto": 7725855.07,
    "descontos": 2375.21,
    "faturamento_apos_descontos": 7723479.86,
    "devolucoes": 717583.36,
    "faturamento_liquido": 7005896.50,
    "quantidade_faturada": 25110,
    "quantidade_devolvida": 1459,
    "quantidade_liquida": 23651,
    "notas_distintas": 16062,
    "ticket_medio_bruto": 481.002058896775,
    "ticket_medio_liquido": 436.1783401817955,
}


@pytest.mark.parametrize("metric,expected", EXPECTED.items())
def test_regression_values_match_notebook(bundle, metric, expected):
    result = compute_kpis(bundle.sales, bundle.returns)
    assert result[metric] == pytest.approx(expected, abs=0.01)


def test_discount_and_return_rates(bundle):
    result = compute_kpis(bundle.sales, bundle.returns)
    assert result["taxa_desconto"] == pytest.approx(2375.21 / 7725855.07)
    assert result["taxa_devolucao_valor"] == pytest.approx(717583.36 / 7723479.86)
    assert result["taxa_devolucao_quantidade"] == pytest.approx(1459 / 25110)


def test_zero_divisions_return_safe_values(bundle):
    result = compute_kpis(bundle.sales.iloc[0:0], bundle.returns.iloc[0:0])
    assert result["ticket_medio_bruto"] == 0
    assert result["ticket_medio_liquido"] == 0
    assert result["taxa_desconto"] == 0
    assert result["taxa_devolucao_valor"] == 0


def test_temporal_reaggregation_recalculates_invoice_count(bundle):
    monthly = aggregate_temporal(bundle.sales, bundle.returns, "Mensal")
    assert len(monthly) == 1
    assert monthly.iloc[0]["notas_distintas"] == 16062
    assert monthly.iloc[0]["ticket_medio_liquido"] == pytest.approx(436.1783401817955)


def test_temporal_totals_reconcile(bundle):
    daily = aggregate_temporal(bundle.sales, bundle.returns, "Diária")
    assert daily["faturamento_bruto"].sum() == pytest.approx(7725855.07)
    assert daily["devolucoes"].sum() == pytest.approx(717583.36)
    assert daily["faturamento_liquido"].sum() == pytest.approx(7005896.50)


def test_product_aggregation_preserves_unit_and_totals(bundle):
    products = aggregate_products(bundle.sales, bundle.returns)
    assert products[["CD_PRODUTO", "CD_ESPECIE"]].duplicated().sum() == 0
    assert products["faturamento_bruto"].sum() == pytest.approx(7725855.07)
    assert products["devolucoes"].sum() == pytest.approx(717583.36)
    assert products["quantidade_liquida"].sum() == pytest.approx(23651)


def test_current_company_aggregation_has_one_billing_company(bundle):
    companies = aggregate_companies(bundle.sales, bundle.returns)
    assert len(companies) == 1
    assert companies.iloc[0]["CD_EMPFAT"] == "6"
    assert companies.iloc[0]["faturamento_liquido"] == pytest.approx(7005896.50)
