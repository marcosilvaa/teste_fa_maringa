"""KPIs e agregações no grão correto."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

from src.config import INVOICE_KEY, OFFICIAL_DATE


KPI_COLUMNS = [
    "faturamento_bruto",
    "descontos",
    "faturamento_apos_descontos",
    "devolucoes",
    "faturamento_liquido",
    "quantidade_faturada",
    "quantidade_devolvida",
    "quantidade_liquida",
    "notas_distintas",
    "ticket_medio_bruto",
    "ticket_medio_liquido",
    "taxa_desconto",
    "taxa_devolucao_valor",
    "taxa_devolucao_quantidade",
]


def safe_divide(numerator: float, denominator: float) -> float:
    return float(numerator / denominator) if denominator else 0.0


def compute_kpis(sales: pd.DataFrame, returns: pd.DataFrame) -> dict[str, float]:
    gross = float(sales["VL_TOTALBRUTO"].sum())
    discount = float(sales["VL_TOTALDESC"].sum())
    after_discount = float(sales["VL_TOTALLIQUIDO"].sum())
    returns_value = float(returns["VL_TOTALLIQUIDO"].sum())
    net = after_discount - returns_value
    billed_qty = float(sales["QT_FATURADO"].sum())
    returned_qty = float(returns["QT_FATURADO"].sum())
    net_qty = billed_qty - returned_qty
    invoices = float(sales[INVOICE_KEY].drop_duplicates().shape[0])

    return {
        "faturamento_bruto": gross,
        "descontos": discount,
        "faturamento_apos_descontos": after_discount,
        "devolucoes": returns_value,
        "faturamento_liquido": net,
        "quantidade_faturada": billed_qty,
        "quantidade_devolvida": returned_qty,
        "quantidade_liquida": net_qty,
        "notas_distintas": invoices,
        "ticket_medio_bruto": safe_divide(gross, invoices),
        "ticket_medio_liquido": safe_divide(net, invoices),
        "taxa_desconto": safe_divide(discount, gross),
        "taxa_devolucao_valor": safe_divide(returns_value, after_discount),
        "taxa_devolucao_quantidade": safe_divide(returned_qty, billed_qty),
    }


def kpis_to_frame(kpis: dict[str, float]) -> pd.DataFrame:
    labels = {
        "faturamento_bruto": "Faturamento bruto",
        "descontos": "Descontos",
        "faturamento_apos_descontos": "Faturamento após descontos",
        "devolucoes": "Devoluções",
        "faturamento_liquido": "Faturamento líquido comercial",
        "quantidade_faturada": "Quantidade faturada",
        "quantidade_devolvida": "Quantidade devolvida",
        "quantidade_liquida": "Quantidade líquida",
        "notas_distintas": "Notas fiscais distintas",
        "ticket_medio_bruto": "Ticket médio bruto",
        "ticket_medio_liquido": "Ticket médio líquido",
        "taxa_desconto": "Taxa de desconto",
        "taxa_devolucao_valor": "Taxa de devolução em valor",
        "taxa_devolucao_quantidade": "Taxa de devolução em quantidade",
    }
    return pd.DataFrame(
        [{"METRICA": labels[key], "VALOR": kpis[key]} for key in KPI_COLUMNS]
    )


def _period_series(dates: pd.Series, granularity: str) -> pd.Series:
    normalized = dates.dt.normalize()
    if granularity == "Diária":
        return normalized
    if granularity == "Semanal":
        return normalized.dt.to_period("W-SUN").dt.start_time
    if granularity == "Mensal":
        return normalized.dt.to_period("M").dt.start_time
    raise ValueError(f"Granularidade inválida: {granularity}")


def _empty_temporal() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "PERIODO",
            "faturamento_bruto",
            "descontos",
            "faturamento_apos_descontos",
            "devolucoes",
            "faturamento_liquido",
            "quantidade_faturada",
            "quantidade_devolvida",
            "quantidade_liquida",
            "notas_distintas",
            "ticket_medio_bruto",
            "ticket_medio_liquido",
            "taxa_devolucao_valor",
        ]
    )


def aggregate_temporal(
    sales: pd.DataFrame,
    returns: pd.DataFrame,
    granularity: str = "Diária",
) -> pd.DataFrame:
    if sales.empty and returns.empty:
        return _empty_temporal()

    sales_work = sales.copy()
    returns_work = returns.copy()
    if not sales_work.empty:
        sales_work["PERIODO"] = _period_series(
            sales_work[OFFICIAL_DATE], granularity
        )
        sales_agg = sales_work.groupby("PERIODO", as_index=False).agg(
            faturamento_bruto=("VL_TOTALBRUTO", "sum"),
            descontos=("VL_TOTALDESC", "sum"),
            faturamento_apos_descontos=("VL_TOTALLIQUIDO", "sum"),
            quantidade_faturada=("QT_FATURADO", "sum"),
        )
        invoices = (
            sales_work[["PERIODO", *INVOICE_KEY]]
            .drop_duplicates()
            .groupby("PERIODO", as_index=False)
            .size()
            .rename(columns={"size": "notas_distintas"})
        )
        sales_agg = sales_agg.merge(invoices, on="PERIODO", validate="one_to_one")
    else:
        sales_agg = pd.DataFrame(columns=["PERIODO"])

    if not returns_work.empty:
        returns_work["PERIODO"] = _period_series(
            returns_work[OFFICIAL_DATE], granularity
        )
        returns_agg = returns_work.groupby("PERIODO", as_index=False).agg(
            devolucoes=("VL_TOTALLIQUIDO", "sum"),
            quantidade_devolvida=("QT_FATURADO", "sum"),
        )
    else:
        returns_agg = pd.DataFrame(columns=["PERIODO"])

    result = sales_agg.merge(returns_agg, on="PERIODO", how="outer")
    numeric_columns = [column for column in result.columns if column != "PERIODO"]
    result[numeric_columns] = result[numeric_columns].fillna(0)

    for required in [
        "faturamento_bruto",
        "descontos",
        "faturamento_apos_descontos",
        "quantidade_faturada",
        "notas_distintas",
        "devolucoes",
        "quantidade_devolvida",
    ]:
        if required not in result:
            result[required] = 0.0

    result["faturamento_liquido"] = (
        result["faturamento_apos_descontos"] - result["devolucoes"]
    )
    result["quantidade_liquida"] = (
        result["quantidade_faturada"] - result["quantidade_devolvida"]
    )
    result["ticket_medio_bruto"] = np.divide(
        result["faturamento_bruto"],
        result["notas_distintas"],
        out=np.zeros(len(result), dtype=float),
        where=result["notas_distintas"].ne(0),
    )
    result["ticket_medio_liquido"] = np.divide(
        result["faturamento_liquido"],
        result["notas_distintas"],
        out=np.zeros(len(result), dtype=float),
        where=result["notas_distintas"].ne(0),
    )
    result["taxa_devolucao_valor"] = np.divide(
        result["devolucoes"],
        result["faturamento_apos_descontos"],
        out=np.zeros(len(result), dtype=float),
        where=result["faturamento_apos_descontos"].ne(0),
    )
    return result.sort_values("PERIODO").reset_index(drop=True)


def _canonical_product_descriptions(
    sales: pd.DataFrame,
    returns: pd.DataFrame,
) -> pd.DataFrame:
    combined = pd.concat(
        [
            sales[["CD_PRODUTO", "CD_ESPECIE", "DS_PRODUTO"]],
            returns[["CD_PRODUTO", "CD_ESPECIE", "DS_PRODUTO"]],
        ],
        ignore_index=True,
    )
    if combined.empty:
        return combined.drop_duplicates(["CD_PRODUTO", "CD_ESPECIE"])
    return (
        combined.fillna({"DS_PRODUTO": "Produto sem descrição"})
        .groupby(["CD_PRODUTO", "CD_ESPECIE", "DS_PRODUTO"], dropna=False)
        .size()
        .rename("FREQUENCIA")
        .reset_index()
        .sort_values(
            ["CD_PRODUTO", "CD_ESPECIE", "FREQUENCIA", "DS_PRODUTO"],
            ascending=[True, True, False, True],
        )
        .drop_duplicates(["CD_PRODUTO", "CD_ESPECIE"])
        [["CD_PRODUTO", "CD_ESPECIE", "DS_PRODUTO"]]
    )


def aggregate_products(sales: pd.DataFrame, returns: pd.DataFrame) -> pd.DataFrame:
    key = ["CD_PRODUTO", "CD_ESPECIE"]
    descriptions = _canonical_product_descriptions(sales, returns)

    sales_agg = sales.groupby(key, as_index=False, dropna=False).agg(
        faturamento_bruto=("VL_TOTALBRUTO", "sum"),
        descontos=("VL_TOTALDESC", "sum"),
        faturamento_apos_descontos=("VL_TOTALLIQUIDO", "sum"),
        quantidade_faturada=("QT_FATURADO", "sum"),
    )
    returns_agg = returns.groupby(key, as_index=False, dropna=False).agg(
        devolucoes=("VL_TOTALLIQUIDO", "sum"),
        quantidade_devolvida=("QT_FATURADO", "sum"),
    )
    result = sales_agg.merge(returns_agg, on=key, how="outer")
    if result.empty:
        return pd.DataFrame(
            columns=[
                *key,
                "DS_PRODUTO",
                "faturamento_bruto",
                "descontos",
                "faturamento_apos_descontos",
                "devolucoes",
                "faturamento_liquido",
                "quantidade_faturada",
                "quantidade_devolvida",
                "quantidade_liquida",
                "valor_liquido_por_unidade",
                "taxa_devolucao_valor",
                "taxa_devolucao_quantidade",
                "ranking_faturamento",
                "ranking_quantidade",
                "participacao_faturamento",
                "participacao_acumulada",
            ]
        )

    numeric = [column for column in result.columns if column not in key]
    result[numeric] = result[numeric].fillna(0)
    result = result.merge(descriptions, on=key, how="left", validate="one_to_one")
    result["faturamento_liquido"] = (
        result["faturamento_apos_descontos"] - result["devolucoes"]
    )
    result["quantidade_liquida"] = (
        result["quantidade_faturada"] - result["quantidade_devolvida"]
    )
    result["valor_liquido_por_unidade"] = np.divide(
        result["faturamento_liquido"],
        result["quantidade_liquida"],
        out=np.full(len(result), np.nan),
        where=result["quantidade_liquida"].ne(0),
    )
    result["taxa_devolucao_valor"] = np.divide(
        result["devolucoes"],
        result["faturamento_apos_descontos"],
        out=np.zeros(len(result), dtype=float),
        where=result["faturamento_apos_descontos"].ne(0),
    )
    result["taxa_devolucao_quantidade"] = np.divide(
        result["quantidade_devolvida"],
        result["quantidade_faturada"],
        out=np.zeros(len(result), dtype=float),
        where=result["quantidade_faturada"].ne(0),
    )
    result["ranking_faturamento"] = result["faturamento_liquido"].rank(
        method="min", ascending=False
    )
    result["ranking_quantidade"] = result["quantidade_liquida"].rank(
        method="min", ascending=False
    )
    total_net = float(result["faturamento_liquido"].sum())
    result["participacao_faturamento"] = (
        result["faturamento_liquido"] / total_net if total_net else 0.0
    )
    result = result.sort_values("faturamento_liquido", ascending=False).reset_index(drop=True)
    result["participacao_acumulada"] = result["participacao_faturamento"].cumsum()
    return result


def aggregate_companies(
    sales: pd.DataFrame,
    returns: pd.DataFrame,
    dimension: str = "CD_EMPFAT",
) -> pd.DataFrame:
    sales_agg = sales.groupby(dimension, as_index=False, dropna=False).agg(
        faturamento_bruto=("VL_TOTALBRUTO", "sum"),
        descontos=("VL_TOTALDESC", "sum"),
        faturamento_apos_descontos=("VL_TOTALLIQUIDO", "sum"),
        quantidade_faturada=("QT_FATURADO", "sum"),
    )
    invoice_columns = list(dict.fromkeys([dimension, *INVOICE_KEY]))
    invoices = (
        sales[invoice_columns]
        .drop_duplicates()
        .groupby(dimension, as_index=False, dropna=False)
        .size()
        .rename(columns={"size": "notas_distintas"})
    )
    sales_agg = sales_agg.merge(invoices, on=dimension, how="left")
    returns_agg = returns.groupby(dimension, as_index=False, dropna=False).agg(
        devolucoes=("VL_TOTALLIQUIDO", "sum"),
        quantidade_devolvida=("QT_FATURADO", "sum"),
    )
    result = sales_agg.merge(returns_agg, on=dimension, how="outer").fillna(0)
    result["faturamento_liquido"] = (
        result["faturamento_apos_descontos"] - result["devolucoes"]
    )
    result["ticket_medio_liquido"] = np.divide(
        result["faturamento_liquido"],
        result["notas_distintas"],
        out=np.zeros(len(result), dtype=float),
        where=result["notas_distintas"].ne(0),
    )
    total = float(result["faturamento_liquido"].sum())
    result["participacao"] = result["faturamento_liquido"] / total if total else 0.0
    return result.sort_values("faturamento_liquido", ascending=False).reset_index(drop=True)


def aggregate_operations(
    sales: pd.DataFrame,
    returns: pd.DataFrame,
    excluded: pd.DataFrame,
) -> pd.DataFrame:
    frames = []
    for classification, frame in [
        ("Venda incluída", sales),
        ("Devolução", returns),
        ("Operação excluída", excluded),
    ]:
        if frame.empty:
            continue
        grouped = frame.groupby("CFOP_TIPO_OPERACAO", as_index=False, dropna=False).agg(
            quantidade_itens=("NR_ITEM", "size"),
            quantidade=("QT_FATURADO", "sum"),
            valor_bruto=("VL_TOTALBRUTO", "sum"),
            descontos=("VL_TOTALDESC", "sum"),
            valor_liquido=("VL_TOTALLIQUIDO", "sum"),
        )
        grouped["classificacao"] = classification
        frames.append(grouped)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True).sort_values(
        "valor_liquido", ascending=False
    )


def aggregate_excluded(excluded: pd.DataFrame) -> pd.DataFrame:
    if excluded.empty:
        return pd.DataFrame(
            columns=["CFOP_TIPO_OPERACAO", "quantidade_itens", "notas_distintas", "valor_liquido"]
        )
    lines = excluded.groupby("CFOP_TIPO_OPERACAO", as_index=False, dropna=False).agg(
        quantidade_itens=("NR_ITEM", "size"),
        valor_liquido=("VL_TOTALLIQUIDO", "sum"),
    )
    notes = (
        excluded[["CFOP_TIPO_OPERACAO", *INVOICE_KEY]]
        .drop_duplicates()
        .groupby("CFOP_TIPO_OPERACAO", as_index=False, dropna=False)
        .size()
        .rename(columns={"size": "notas_distintas"})
    )
    return lines.merge(notes, on="CFOP_TIPO_OPERACAO", validate="one_to_one").sort_values(
        "valor_liquido", ascending=False
    )


def participation(values: Sequence[float], top_n: int) -> float:
    series = pd.Series(values, dtype=float).sort_values(ascending=False)
    total = float(series.sum())
    return safe_divide(float(series.head(top_n).sum()), total)
