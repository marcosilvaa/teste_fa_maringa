"""Comparação empresarial e auditoria das operações."""

import pandas as pd
import streamlit as st

from src.charts import company_revenue, excluded_operations, operation_composition
from src.filters import apply_filters
from src.formatting import format_brl, format_percentage, format_quantity
from src.metrics import (
    aggregate_companies,
    aggregate_excluded,
    aggregate_operations,
    compute_kpis,
)
from src.ui import (
    get_bundle_or_stop,
    metric_grid,
    page_header,
    render_filters,
    section_title,
    setup_page,
    show_chart,
    show_empty_state,
)


setup_page("Empresas e Operações", "◇")
bundle = get_bundle_or_stop()
spec = render_filters(
    bundle,
    "companies",
    include=(
        "date",
        "billing_company",
        "source_company",
        "operation",
        "tipi_group",
        "tipi_family",
        "item_type",
    ),
)
filtered = apply_filters(bundle, spec)

page_header(
    "05 · Estrutura operacional",
    "Empresas e Operações",
    "Participação empresarial e movimentos fiscais incluídos ou excluídos do faturamento.",
)

if filtered.empty:
    show_empty_state()
    st.stop()

dimension = st.radio(
    "Dimensão empresarial",
    ["CD_EMPFAT", "CD_EMPRESA"],
    horizontal=True,
    help="Empresa de faturamento ou empresa de origem.",
)
companies = aggregate_companies(filtered.sales, filtered.returns, dimension)
operations = aggregate_operations(filtered.sales, filtered.returns, filtered.excluded)
excluded = aggregate_excluded(filtered.excluded)
kpis = compute_kpis(filtered.sales, filtered.returns)

metric_grid(
    [
        ("Faturamento bruto", format_brl(kpis["faturamento_bruto"]), "Operações de venda no recorte."),
        ("Faturamento líquido", format_brl(kpis["faturamento_liquido"]), "Após descontos e devoluções."),
        ("Devoluções", format_brl(kpis["devolucoes"]), "Movimentos classificados como devolução."),
        ("Notas distintas", format_quantity(kpis["notas_distintas"]), "Notas com item de venda."),
        ("Ticket médio", format_brl(kpis["ticket_medio_liquido"]), "Recalculado no recorte."),
        ("Empresas no recorte", format_quantity(len(companies)), dimension),
    ],
    columns=3,
)

section_title("Empresas")
if len(companies) <= 1:
    st.info("O recorte possui uma única empresa; um gráfico comparativo seria enganoso.")
    st.dataframe(companies, width="stretch", hide_index=True)
else:
    show_chart(company_revenue(companies, dimension))

section_title("Tipos de operação")
show_chart(operation_composition(operations))
st.dataframe(operations, width="stretch", hide_index=True)

section_title("Operações fora do faturamento")
if excluded.empty:
    st.info("Nenhuma operação excluída atende aos filtros atuais.")
else:
    show_chart(excluded_operations(excluded))
    st.dataframe(excluded, width="stretch", hide_index=True)

section_title("CD_EMPRESA × CD_EMPFAT")
combined = pd.concat([filtered.sales, filtered.returns, filtered.excluded], ignore_index=True)
comparison = (
    combined.groupby(["CD_EMPRESA", "CD_EMPFAT"], as_index=False, dropna=False)
    .agg(quantidade_itens=("NR_ITEM", "size"), valor_movimentado=("VL_TOTALLIQUIDO", "sum"))
    .sort_values("valor_movimentado", ascending=False)
)
st.dataframe(comparison, width="stretch", hide_index=True)
