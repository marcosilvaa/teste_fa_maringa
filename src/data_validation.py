"""Validações estruturais que protegem os indicadores."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from src.config import INVOICE_KEY, ITEM_KEY, JOIN_KEY, OFFICIAL_DATE
from src.exceptions import CardinalityError, SchemaValidationError


def validate_required_columns(
    df: pd.DataFrame,
    required: Iterable[str],
    source_name: str,
) -> None:
    missing = sorted(set(required) - set(df.columns))
    if missing:
        raise SchemaValidationError(
            f"{source_name}: colunas obrigatórias ausentes: {', '.join(missing)}. "
            "O pipeline não pode calcular métricas confiáveis."
        )


def validate_key_not_null(df: pd.DataFrame, key: list[str], source_name: str) -> None:
    null_rows = int(df[key].isna().any(axis=1).sum())
    if null_rows:
        raise CardinalityError(
            f"{source_name}: {null_rows} registro(s) com nulo na chave {key}."
        )


def validate_unique_key(df: pd.DataFrame, key: list[str], source_name: str) -> None:
    duplicated = int(df.duplicated(key).sum())
    if duplicated:
        raise CardinalityError(
            f"{source_name}: chave {key} possui {duplicated} duplicidade(s); "
            "cardinalidade many_to_one não é confiável."
        )


def validate_dates(nf: pd.DataFrame, items: pd.DataFrame) -> None:
    invalid_nf_join = int(nf["DT_FATURA"].isna().sum())
    invalid_item_join = int(items["DT_FATURA"].isna().sum())
    invalid_official = int(nf[OFFICIAL_DATE].isna().sum())
    if invalid_nf_join or invalid_item_join or invalid_official:
        raise SchemaValidationError(
            "Datas inválidas impedem integração ou análise temporal: "
            f"NF.DT_FATURA={invalid_nf_join}, "
            f"NFITEM.DT_FATURA={invalid_item_join}, "
            f"NF.{OFFICIAL_DATE}={invalid_official}."
        )


def validate_numeric_columns(df: pd.DataFrame, columns: list[str], source_name: str) -> None:
    invalid = {column: int(df[column].isna().sum()) for column in columns}
    invalid = {column: count for column, count in invalid.items() if count}
    if invalid:
        details = ", ".join(f"{column}={count}" for column, count in invalid.items())
        raise SchemaValidationError(
            f"{source_name}: nulos ou valores numéricos inválidos: {details}."
        )


def validate_source_structure(nf: pd.DataFrame, items: pd.DataFrame) -> None:
    validate_key_not_null(nf, JOIN_KEY, "NF")
    validate_key_not_null(items, ITEM_KEY, "NFITEM")
    validate_unique_key(nf, JOIN_KEY, "NF")
    validate_unique_key(items, ITEM_KEY, "NFITEM")
    validate_dates(nf, items)
    validate_numeric_columns(
        items,
        ["QT_FATURADO", "VL_TOTALBRUTO", "VL_TOTALDESC", "VL_TOTALLIQUIDO"],
        "NFITEM",
    )


def count_repeated_invoice_numbers(nf: pd.DataFrame) -> int:
    return int(nf.duplicated(INVOICE_KEY).sum())
