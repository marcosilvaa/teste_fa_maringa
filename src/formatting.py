"""Formatação pt-BR e exportação compatível com Excel."""

from __future__ import annotations

from datetime import date, datetime

import pandas as pd


FRIENDLY_COLUMNS = {
    "PERIODO": "Período",
    "CD_PRODUTO": "Código do produto",
    "DS_PRODUTO": "Produto",
    "CD_ESPECIE": "Unidade",
    "CD_EMPRESA": "Empresa de origem",
    "CD_EMPFAT": "Empresa de faturamento",
    "CFOP_TIPO_OPERACAO": "Tipo de operação",
    "faturamento_bruto": "Faturamento bruto",
    "descontos": "Descontos",
    "faturamento_apos_descontos": "Faturamento após descontos",
    "devolucoes": "Devoluções",
    "faturamento_liquido": "Faturamento líquido",
    "quantidade_faturada": "Quantidade faturada",
    "quantidade_devolvida": "Quantidade devolvida",
    "quantidade_liquida": "Quantidade líquida",
    "notas_distintas": "Notas distintas",
    "ticket_medio_bruto": "Ticket médio bruto",
    "ticket_medio_liquido": "Ticket médio líquido",
    "taxa_devolucao_valor": "Taxa de devolução em valor",
    "taxa_devolucao_quantidade": "Taxa de devolução em quantidade",
    "valor_liquido_por_unidade": "Valor líquido por unidade",
    "ranking_faturamento": "Ranking por faturamento",
    "ranking_quantidade": "Ranking por quantidade",
    "participacao_faturamento": "Participação no faturamento",
    "participacao_acumulada": "Participação acumulada",
}


def format_brl(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_quantity(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "—"
    number = float(value)
    decimals = 0 if number.is_integer() else 2
    formatted = f"{number:,.{decimals}f}"
    return formatted.replace(",", "X").replace(".", ",").replace("X", ".")


def format_percentage(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"{float(value):.2%}".replace(".", ",")


def format_date(value: date | datetime | pd.Timestamp | None) -> str:
    if value is None or pd.isna(value):
        return "—"
    return pd.Timestamp(value).strftime("%d/%m/%Y")


def friendly_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(columns=FRIENDLY_COLUMNS)


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    export = friendly_dataframe(df.copy())
    for column in export.select_dtypes(include=["datetime", "datetimetz"]).columns:
        export[column] = export[column].dt.strftime("%d/%m/%Y")
    text = export.to_csv(index=False, sep=";", decimal=",")
    return text.encode("utf-8-sig")
