"""Análise comercial no nível de produto e unidade."""

import streamlit as st

from src.charts import (
    product_scatter,
    revenue_by_unit,
    top_products_quantity,
    top_products_revenue,
)
from src.filters import apply_filters
from src.formatting import format_brl, format_percentage, format_quantity
from src.metrics import aggregate_products, participation
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


setup_page("Produtos", "▦")
bundle = get_bundle_or_stop()
spec = render_filters(bundle, "products")
filtered = apply_filters(bundle, spec)

page_header(
    "03 · Portfólio",
    "Produtos",
    "Receita, volume e devoluções no grão CD_PRODUTO + CD_ESPECIE, preservando a comparabilidade das unidades.",
)

products = aggregate_products(filtered.sales, filtered.returns)
if products.empty:
    show_empty_state()
    st.stop()

sold = products.loc[products["quantidade_faturada"] > 0]
top_revenue = sold.nlargest(1, "faturamento_liquido").iloc[0]
top_quantity = sold.nlargest(1, "quantidade_liquida").iloc[0]
average_revenue = float(sold["faturamento_liquido"].mean())

metric_grid(
    [
        ("Produtos vendidos", format_quantity(len(sold)), "Combinações produto + unidade com venda."),
        ("Maior faturamento", format_brl(top_revenue["faturamento_liquido"]), str(top_revenue["DS_PRODUTO"])),
        ("Faturamento médio por produto", format_brl(average_revenue), "Média do faturamento líquido por produto + unidade."),
        ("Maior quantidade", format_quantity(top_quantity["quantidade_liquida"]), f"{top_quantity['DS_PRODUTO']} · {top_quantity['CD_ESPECIE']}"),
        ("Participação Top 5", format_percentage(participation(products["faturamento_liquido"], 5)), "Sobre faturamento líquido de produtos."),
        ("Participação Top 10", format_percentage(participation(products["faturamento_liquido"], 10)), "Sobre faturamento líquido de produtos."),
    ],
    columns=3,
)

section_title("Rankings")
show_chart(top_products_revenue(products, 10))
show_chart(top_products_quantity(products, 10))

section_title("Relação entre volume e valor")
show_chart(product_scatter(products))
show_chart(revenue_by_unit(products))

section_title("Tabela analítica")
display_columns = [
    "CD_PRODUTO",
    "DS_PRODUTO",
    "CD_ESPECIE",
    "faturamento_bruto",
    "descontos",
    "devolucoes",
    "faturamento_liquido",
    "quantidade_faturada",
    "quantidade_devolvida",
    "quantidade_liquida",
    "valor_liquido_por_unidade",
    "ranking_faturamento",
    "ranking_quantidade",
    "participacao_faturamento",
    "participacao_acumulada",
]
st.dataframe(products[display_columns], width="stretch", hide_index=True)
