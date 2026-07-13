"""Filtros consistentes para vendas, devoluções e auditoria."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd

from src.config import OFFICIAL_DATE
from src.models import AnalyticalBundle, FilteredBundle


@dataclass(frozen=True, slots=True)
class FilterSpec:
    start_date: date | None = None
    end_date: date | None = None
    billing_companies: tuple[str, ...] = ()
    source_companies: tuple[str, ...] = ()
    operations: tuple[str, ...] = ()
    product_codes: tuple[str, ...] = ()
    description_query: str = ""
    units: tuple[str, ...] = ()
    tipi_groups: tuple[str, ...] = ()
    tipi_families: tuple[str, ...] = ()
    item_types: tuple[str, ...] = ()


def _filter_frame(df: pd.DataFrame, spec: FilterSpec) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    mask = pd.Series(True, index=df.index)
    if spec.start_date is not None:
        mask &= df[OFFICIAL_DATE].ge(pd.Timestamp(spec.start_date))
    if spec.end_date is not None:
        mask &= df[OFFICIAL_DATE].le(pd.Timestamp(spec.end_date))
    if spec.billing_companies:
        mask &= df["CD_EMPFAT"].isin(spec.billing_companies)
    if spec.source_companies:
        mask &= df["CD_EMPRESA"].isin(spec.source_companies)
    if spec.operations:
        mask &= df["CFOP_TIPO_OPERACAO"].isin(spec.operations)
    if spec.product_codes:
        mask &= df["CD_PRODUTO"].isin(spec.product_codes)
    if spec.units:
        mask &= df["CD_ESPECIE"].isin(spec.units)
    if spec.tipi_groups:
        mask &= df["TIPI_GRUPO_FISCAL"].isin(spec.tipi_groups)
    if spec.tipi_families:
        mask &= df["TIPI_FAMILIA_COMERCIAL"].isin(spec.tipi_families)
    if spec.item_types:
        mask &= df["TIPO_ITEM_FISCAL"].isin(spec.item_types)
    query = spec.description_query.strip()
    if query:
        mask &= df["DS_PRODUTO"].fillna("").str.contains(
            query,
            case=False,
            regex=False,
        )
    return df.loc[mask].copy()


def apply_filters(bundle: AnalyticalBundle, spec: FilterSpec) -> FilteredBundle:
    """Aplica exatamente o mesmo contrato aos três universos."""

    return FilteredBundle(
        sales=_filter_frame(bundle.sales, spec),
        returns=_filter_frame(bundle.returns, spec),
        excluded=_filter_frame(bundle.excluded, spec),
    )


def filter_options(bundle: AnalyticalBundle) -> dict[str, list[str]]:
    """Valores disponíveis, derivados dos dados válidos."""

    data = bundle.integrated

    def values(column: str) -> list[str]:
        return sorted(data[column].dropna().astype(str).unique().tolist())

    return {
        "billing_companies": values("CD_EMPFAT"),
        "source_companies": values("CD_EMPRESA"),
        "operations": values("CFOP_TIPO_OPERACAO"),
        "product_codes": values("CD_PRODUTO"),
        "units": values("CD_ESPECIE"),
        "tipi_groups": values("TIPI_GRUPO_FISCAL"),
        "tipi_families": values("TIPI_FAMILIA_COMERCIAL"),
        "item_types": values("TIPO_ITEM_FISCAL"),
    }
