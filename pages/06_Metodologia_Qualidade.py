"""Metodologia, qualidade e auditoria somente leitura."""

import pandas as pd
import streamlit as st

from src.charts import excluded_operations
from src.config import INVOICE_KEY, JOIN_KEY, OFFICIAL_DATE, SALES_OPERATIONS
from src.formatting import format_date, format_quantity
from src.metrics import aggregate_excluded
from src.ui import get_bundle_or_stop, page_header, section_title, setup_page, show_chart


setup_page("Metodologia e Qualidade", "✓")
bundle = get_bundle_or_stop()

page_header(
    "06 · Governança analítica",
    "Metodologia e Qualidade",
    "Regras, controles estruturais e movimentos excluídos. Esta página é somente informativa e não altera os dados.",
)

section_title("Metodologia aplicada")
methodology = [
    ("Nota válida", "Somente TP_SITUACAO = E."),
    ("Chave de integração", " + ".join(JOIN_KEY)),
    ("Cardinalidade", "Muitos itens para um cabeçalho, validada como many_to_one."),
    ("Operações de venda", ", ".join(SALES_OPERATIONS)),
    ("Devoluções", "CFOP_TIPO_OPERACAO = DEVOLUCAO, fluxo ENTRADA e item PRODUTO."),
    ("Data oficial", OFFICIAL_DATE),
    ("Nota distinta", " + ".join(INVOICE_KEY) + ", somente documentos com venda."),
    ("Faturamento líquido", "Vendas após descontos menos devoluções; métrica comercial, não contábil após tributos."),
    ("Quantidade", "Calculada no item e preservada por CD_ESPECIE nas comparações de produto."),
    ("Cache", "Assinatura por caminho, tamanho e mtime dos CSVs; alteração invalida o processamento."),
    ("Parquet", "Não criado nesta versão; CSV permanece origem oficial e o volume atual não exige materialização."),
]
st.dataframe(pd.DataFrame(methodology, columns=["TEMA", "REGRA"]), width="stretch", hide_index=True)

section_title("Qualidade dos dados")
st.dataframe(bundle.quality, width="stretch", hide_index=True)

quality = bundle.quality.set_index("INDICADOR")["VALOR"]
columns = st.columns(4)
columns[0].metric("Notas originais", format_quantity(quality["Notas originais"]))
columns[1].metric("Notas efetivadas", format_quantity(quality["Notas efetivadas"]))
columns[2].metric("Itens ligados", format_quantity(quality["Itens ligados a notas válidas"]))
columns[3].metric("Inconsistências de fluxo", format_quantity(quality["Inconsistências de fluxo"]))

section_title("Cobertura temporal")
date_summary = pd.DataFrame(
    [
        ("DT_EMISSAO", bundle.nf["DT_EMISSAO"].min(), bundle.nf["DT_EMISSAO"].max(), bundle.nf["DT_EMISSAO"].isna().sum()),
        ("DT_FATURA", bundle.nf["DT_FATURA"].min(), bundle.nf["DT_FATURA"].max(), bundle.nf["DT_FATURA"].isna().sum()),
    ],
    columns=["CAMPO", "DATA_MINIMA", "DATA_MAXIMA", "NULOS"],
)
st.dataframe(date_summary, width="stretch", hide_index=True)

section_title("Nulos nas colunas essenciais")
essential = [
    *JOIN_KEY,
    "DT_EMISSAO",
    "NR_NF",
    "CD_SERIE",
    "CD_PRODUTO",
    "DS_PRODUTO",
    "CD_ESPECIE",
    "QT_FATURADO",
    "VL_TOTALBRUTO",
    "VL_TOTALDESC",
    "VL_TOTALLIQUIDO",
]
nulls = (
    bundle.integrated[essential]
    .isna()
    .sum()
    .rename_axis("COLUNA")
    .reset_index(name="NULOS")
    .sort_values("NULOS", ascending=False)
)
st.dataframe(nulls, width="stretch", hide_index=True)

section_title("Consistência de fluxo")
if bundle.flow_issues.empty:
    st.success("Nenhuma inconsistência entre TP_OPERACAO e CFOP_TIPO_FLUXO.")
else:
    st.error(f"Foram identificadas {len(bundle.flow_issues):,} inconsistências de fluxo.".replace(",", "."))
    st.dataframe(bundle.flow_issues, width="stretch", hide_index=True)

section_title("Auditoria das operações excluídas")
excluded = aggregate_excluded(bundle.excluded)
show_chart(excluded_operations(excluded))
st.dataframe(excluded, width="stretch", hide_index=True)
