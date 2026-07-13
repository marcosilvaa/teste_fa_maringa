"""Estruturas que transportam dados entre camadas."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(slots=True)
class AnalyticalBundle:
    """Bases produzidas uma vez pelo pipeline central."""

    nf: pd.DataFrame
    items: pd.DataFrame
    valid_nf: pd.DataFrame
    integrated: pd.DataFrame
    sales: pd.DataFrame
    returns: pd.DataFrame
    excluded: pd.DataFrame
    unmatched_items: pd.DataFrame
    flow_issues: pd.DataFrame
    quality: pd.DataFrame


@dataclass(slots=True)
class FilteredBundle:
    """Recorte coerente consumido por uma página."""

    sales: pd.DataFrame
    returns: pd.DataFrame
    excluded: pd.DataFrame

    @property
    def empty(self) -> bool:
        return self.sales.empty and self.returns.empty and self.excluded.empty
