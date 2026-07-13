"""Diagnóstico de devoluções e materialidade."""

import numpy as np
import streamlit as st

from src.charts import (
    return_ranking,
    returns_evolution,
    sales_vs_returns,
)
from src.filters import apply_filters
from src.formatting import format_brl, format_date, format_percentage, format_quantity
from src.metrics import aggregate_products, aggregate_temporal, compute_kpis
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


setup_page("Devoluções", "↩")
bundle = get_bundle_or_stop()
spec = render_filters(bundle, "returns")
filtered = apply_filters(bundle, spec)

page_header(
    "04 · Ponto crítico",
    "Devoluções",
    "Materialidade, concentração e taxas de retorno com cortes mínimos para evitar falsos sinais em volumes irrelevantes.",
)

products = aggregate_products(filtered.sales, filtered.returns)
temporal = aggregate_temporal(filtered.sales, filtered.returns)
kpis = compute_kpis(filtered.sales, filtered.returns)
if products.empty or temporal.empty:
    show_empty_state()
    st.stop()

min_billed_qty = 10.0
min_revenue = 1000.0
min_returns = 100.0
risk_threshold = 0.10

material = products.loc[
    products["quantidade_faturada"].ge(min_billed_qty)
    & products["faturamento_apos_descontos"].ge(min_revenue)
    & products["devolucoes"].ge(min_returns)
].copy()

top_return = products.nlargest(1, "devolucoes").iloc[0]
if not material.empty:
    top_rate = material.nlargest(1, "taxa_devolucao_valor").iloc[0]
    top_rate_value = format_percentage(top_rate["taxa_devolucao_valor"])
    top_rate_help = str(top_rate["DS_PRODUTO"])
else:
    top_rate_value = "Sem produto elegível"
    top_rate_help = "Ajuste os cortes mínimos."
top_day = temporal.nlargest(1, "devolucoes").iloc[0]

metric_grid(
    [
        ("Valor devolvido", format_brl(kpis["devolucoes"]), "VL_TOTALLIQUIDO das devoluções."),
        ("Quantidade devolvida", format_quantity(kpis["quantidade_devolvida"]), "QT_FATURADO das devoluções."),
        ("Taxa em valor", format_percentage(kpis["taxa_devolucao_valor"]), "Devoluções / vendas após descontos."),
        ("Taxa em quantidade", format_percentage(kpis["taxa_devolucao_quantidade"]), "Quantidade devolvida / faturada."),
        ("Maior valor devolvido", format_brl(top_return["devolucoes"]), str(top_return["DS_PRODUTO"])),
        ("Maior taxa material", top_rate_value, top_rate_help),
        ("Maior dia", format_brl(top_day["devolucoes"]), format_date(top_day["PERIODO"])),
    ],
    columns=4,
)

section_title("Evolução das devoluções")
show_chart(returns_evolution(temporal))

section_title("Produtos com devolução")
show_chart(return_ranking(products, "devolucoes", "Top produtos por valor devolvido"))
show_chart(
    return_ranking(
        products,
        "quantidade_devolvida",
        "Top produtos por quantidade devolvida",
        quantity=True,
    )
)

if material.empty:
    st.info("Nenhum produto atende aos controles mínimos para ranking por taxa.")
else:
    show_chart(
        return_ranking(
            material,
            "taxa_devolucao_valor",
            "Taxa de devolução em valor — produtos materiais",
            percentage=True,
        )
    )
    show_chart(
        return_ranking(
            material,
            "taxa_devolucao_quantidade",
            "Taxa de devolução em quantidade — produtos materiais",
            percentage=True,
        )
    )

show_chart(sales_vs_returns(products))

section_title("Tabela de risco")
risk_table = products.loc[products["devolucoes"] > 0].copy()
risk_table["RISCO"] = np.select(
    [
        risk_table["taxa_devolucao_valor"].ge(max(0.30, risk_threshold)),
        risk_table["taxa_devolucao_valor"].ge(max(0.20, risk_threshold)),
        risk_table["taxa_devolucao_valor"].ge(risk_threshold),
    ],
    ["Crítico", "Alto", "Atenção"],
    default="Monitorar",
)
columns = [
    "CD_PRODUTO",
    "DS_PRODUTO",
    "CD_ESPECIE",
    "quantidade_faturada",
    "quantidade_devolvida",
    "taxa_devolucao_quantidade",
    "faturamento_apos_descontos",
    "devolucoes",
    "taxa_devolucao_valor",
    "faturamento_liquido",
    "RISCO",
]
st.dataframe(risk_table[columns], width="stretch", hide_index=True)
