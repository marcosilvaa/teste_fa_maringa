"""Entrada da aplicação Streamlit multipágina."""

from src.filters import FilterSpec, apply_filters
from src.formatting import format_brl, format_percentage, format_quantity
from src.metrics import compute_kpis
from src.ui import get_bundle_or_stop, metric_grid, page_header, section_title, setup_page

import streamlit as st


setup_page("Início", "◫")
bundle = get_bundle_or_stop()
filtered = apply_filters(bundle, FilterSpec())
kpis = compute_kpis(filtered.sales, filtered.returns)

page_header(
    "F.A. Maringá · Inteligência comercial",
    "Faturamento em perspectiva",
    "Aplicação executiva e auditável para acompanhar vendas, descontos, devoluções, produtos, empresas e qualidade fiscal.",
)

metric_grid(
    [
        ("Faturamento bruto", format_brl(kpis["faturamento_bruto"]), "Vendas antes de descontos e devoluções."),
        ("Faturamento líquido", format_brl(kpis["faturamento_liquido"]), "Líquido comercial, não receita contábil após tributos."),
        ("Devoluções", format_brl(kpis["devolucoes"]), "Valor líquido dos itens devolvidos."),
        ("Taxa de devolução", format_percentage(kpis["taxa_devolucao_valor"]), "Devoluções sobre vendas após descontos."),
        ("Quantidade líquida", format_quantity(kpis["quantidade_liquida"]), "Quantidade faturada menos devolvida."),
        ("Notas distintas", format_quantity(kpis["notas_distintas"]), "CD_EMPFAT + CD_SERIE + NR_NF."),
        ("Ticket médio líquido", format_brl(kpis["ticket_medio_liquido"]), "Líquido dividido pelas notas de venda."),
        ("Ticket médio bruto", format_brl(kpis["ticket_medio_bruto"]), "Bruto dividido pelas notas de venda."),
    ]
)

section_title("Navegue pela análise", "Cada página mantém regras e filtros no mesmo núcleo analítico.")
links = [
    ("pages/01_Visao_Geral.py", "Visão Geral", "KPIs, tendências, composição e destaques."),
    ("pages/03_Produtos.py", "Produtos", "Receita, volume, Pareto e valor por unidade."),
    ("pages/04_Devolucoes.py", "Devoluções", "Produtos críticos, taxas e controles de materialidade."),
    ("pages/05_Empresas_Operacoes.py", "Empresas e Operações", "Empresas, CFOPs e movimentos fora da receita."),
    ("pages/06_Metodologia_Qualidade.py", "Metodologia e Qualidade", "Regras, chaves, controles e auditoria."),
]
for start in range(0, len(links), 3):
    columns = st.columns(3)
    for column, (path, label, description) in zip(columns, links[start : start + 3]):
        with column:
            st.markdown(f"**{label}**")
            st.caption(description)
            st.page_link(path, label="Abrir página", width="stretch")
