"""Visão executiva consolidada."""

from html import escape

import streamlit as st

from src.charts import (
    cumulative_revenue,
    operation_composition,
    returns_evolution,
    revenue_evolution,
    revenue_waterfall,
    top_products_revenue,
)
from src.filters import apply_filters
from src.formatting import format_brl, format_date, format_percentage, format_quantity
from src.metrics import (
    aggregate_operations,
    aggregate_products,
    aggregate_temporal,
    compute_kpis,
    participation,
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


setup_page("Visão Geral", "◩")
bundle = get_bundle_or_stop()
spec = render_filters(bundle, "overview")
filtered = apply_filters(bundle, spec)

page_header(
    "01 · Síntese executiva",
    "Visão Geral",
    "Leitura consolidada do faturamento comercial após descontos e devoluções, sempre no recorte selecionado.",
)

if filtered.sales.empty and filtered.returns.empty:
    show_empty_state()
    st.stop()

kpis = compute_kpis(filtered.sales, filtered.returns)
temporal = aggregate_temporal(filtered.sales, filtered.returns)
daily_average = float(temporal["faturamento_liquido"].mean())

metric_grid(
    [
        ("Faturamento bruto", format_brl(kpis["faturamento_bruto"]), "Soma de VL_TOTALBRUTO nas vendas."),
        ("Faturamento líquido", format_brl(kpis["faturamento_liquido"]), "Após descontos e devoluções."),
        ("Descontos", format_brl(kpis["descontos"]), "Somente descontos das vendas."),
        ("Devoluções", format_brl(kpis["devolucoes"]), "Valor líquido devolvido."),
        ("Quantidade faturada", format_quantity(kpis["quantidade_faturada"]), "Itens de venda."),
        ("Quantidade líquida", format_quantity(kpis["quantidade_liquida"]), "Faturada menos devolvida."),
        ("Notas distintas", format_quantity(kpis["notas_distintas"]), "Somente notas com item de venda."),
        ("Ticket médio líquido", format_brl(kpis["ticket_medio_liquido"]), "Recalculado no filtro atual."),
        ("Taxa de devolução", format_percentage(kpis["taxa_devolucao_valor"]), "Devoluções / vendas após descontos."),
        ("Média diária", format_brl(daily_average), "Média do faturamento líquido por dia."),
        (
            "Participação dos 5 maiores períodos",
            format_percentage(participation(temporal["faturamento_liquido"], 5)),
            "Concentração do faturamento líquido nos cinco maiores dias.",
        ),
        (
            "Participação dos 10 maiores períodos",
            format_percentage(participation(temporal["faturamento_liquido"], 10)),
            "Concentração do faturamento líquido nos dez maiores dias.",
        ),
    ],
    columns=3,
)

products = aggregate_products(filtered.sales, filtered.returns)
operations = aggregate_operations(filtered.sales, filtered.returns, filtered.excluded)

section_title("Destaques")
highlights: list[tuple[str, str]] = []
if not temporal.empty:
    highest = temporal.loc[temporal["faturamento_liquido"].idxmax()]
    lowest = temporal.loc[temporal["faturamento_liquido"].idxmin()]
    highlights.extend(
        [
            ("Maior dia", f"{format_date(highest['PERIODO'])} · {format_brl(highest['faturamento_liquido'])}"),
            ("Menor dia", f"{format_date(lowest['PERIODO'])} · {format_brl(lowest['faturamento_liquido'])}"),
        ]
    )
if not products.empty:
    top_product = products.loc[products["faturamento_liquido"].idxmax()]
    top_return = products.loc[products["devolucoes"].idxmax()]
    highlights.extend(
        [
            ("Produto líder", f"{escape(str(top_product['DS_PRODUTO']))} · {format_brl(top_product['faturamento_liquido'])}"),
            ("Maior devolução", f"{escape(str(top_return['DS_PRODUTO']))} · {format_brl(top_return['devolucoes'])}"),
        ]
    )
for start in range(0, len(highlights), 2):
    columns = st.columns(2)
    for column, (title, value) in zip(columns, highlights[start : start + 2]):
        column.markdown(
            f"<div class='highlight-card'><strong>{title}</strong><span>{value}</span></div>",
            unsafe_allow_html=True,
        )

section_title("Faturamento no tempo")
revenue_chart = revenue_evolution(temporal)
returns_chart = returns_evolution(temporal)
returns_chart.update_layout(height=revenue_chart.layout.height)

left, right = st.columns([1.65, 1])
with left:
    show_chart(revenue_chart)
with right:
    show_chart(returns_chart)

show_chart(cumulative_revenue(temporal))

section_title("Composição e concentração")

waterfall_chart = revenue_waterfall(kpis)
composition_chart = operation_composition(operations, included_only=True)
composition_chart.update_layout(height=waterfall_chart.layout.height)

left, right = st.columns(2)
with left:
    show_chart(waterfall_chart)
with right:
    show_chart(composition_chart)

show_chart(top_products_revenue(products, 10))

section_title("Tabela temporal detalhada")
st.dataframe(
    temporal,
    width="stretch",
    hide_index=True,
    column_config={
        "PERIODO": st.column_config.DateColumn("Período", format="DD/MM/YYYY"),
        "faturamento_bruto": st.column_config.NumberColumn("Faturamento bruto", format="R$ %.2f"),
        "descontos": st.column_config.NumberColumn("Descontos", format="R$ %.2f"),
        "faturamento_apos_descontos": st.column_config.NumberColumn(
            "Faturamento após descontos", format="R$ %.2f"
        ),
        "devolucoes": st.column_config.NumberColumn("Devoluções", format="R$ %.2f"),
        "faturamento_liquido": st.column_config.NumberColumn("Faturamento líquido", format="R$ %.2f"),
        "quantidade_faturada": st.column_config.NumberColumn("Quantidade faturada", format="%.0f"),
        "quantidade_devolvida": st.column_config.NumberColumn("Quantidade devolvida", format="%.0f"),
        "quantidade_liquida": st.column_config.NumberColumn("Quantidade líquida", format="%.0f"),
        "notas_distintas": st.column_config.NumberColumn("Notas distintas", format="%.0f"),
        "ticket_medio_bruto": st.column_config.NumberColumn("Ticket médio bruto", format="R$ %.2f"),
        "ticket_medio_liquido": st.column_config.NumberColumn("Ticket médio líquido", format="R$ %.2f"),
        "taxa_devolucao_valor": st.column_config.NumberColumn("Taxa de devolução", format="percent"),
    },
)
