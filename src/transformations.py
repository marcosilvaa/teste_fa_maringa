"""Pipeline único de elegibilidade, integração e classificação."""

from __future__ import annotations

import numpy as np
import pandas as pd
from pandas.errors import MergeError

from src.config import (
    INVOICE_KEY,
    JOIN_KEY,
    REQUIRED_ITEM_COLUMNS,
    REQUIRED_NF_COLUMNS,
    RETURN_OPERATION,
    SALES_OPERATIONS,
)
from src.data_validation import (
    count_repeated_invoice_numbers,
    validate_required_columns,
    validate_source_structure,
)
from src.exceptions import CardinalityError
from src.models import AnalyticalBundle


HEADER_ATTRIBUTES = [
    "DT_EMISSAO",
    "NR_NF",
    "CD_SERIE",
    "CD_PESSOA",
    "TP_OPERACAO",
    "TP_SITUACAO",
    "CD_OPERACAO",
]


def _build_quality(
    nf: pd.DataFrame,
    items: pd.DataFrame,
    valid_nf: pd.DataFrame,
    integrated: pd.DataFrame,
    unmatched_items: pd.DataFrame,
    flow_issues: pd.DataFrame,
) -> pd.DataFrame:
    metrics = [
        ("Notas originais", len(nf), "Cabeçalhos antes dos filtros"),
        ("Notas efetivadas", len(valid_nf), "TP_SITUACAO = E"),
        ("Itens originais", len(items), "Itens antes dos filtros"),
        ("Itens ligados a notas válidas", len(integrated), "Merge many_to_one"),
        (
            "Itens removidos por nota não efetivada",
            len(unmatched_items),
            "Sem cabeçalho efetivado correspondente",
        ),
        ("Duplicidades na chave de integração", int(nf.duplicated(JOIN_KEY).sum()), "NF"),
        ("Notas com numeração repetida", count_repeated_invoice_numbers(valid_nf), "Chave fiscal"),
        ("Registros sem data oficial", int(valid_nf["DT_EMISSAO"].isna().sum()), "DT_EMISSAO"),
        (
            "Registros sem produto",
            int(integrated[["CD_PRODUTO", "DS_PRODUTO"]].isna().any(axis=1).sum()),
            "Itens válidos",
        ),
        (
            "Registros sem empresa",
            int(integrated[["CD_EMPRESA", "CD_EMPFAT"]].isna().any(axis=1).sum()),
            "Itens válidos",
        ),
        ("Inconsistências de fluxo", len(flow_issues), "Cabeçalho versus CFOP"),
    ]
    return pd.DataFrame(metrics, columns=["INDICADOR", "VALOR", "CONTEXTO"])


def prepare_analytical_data(nf: pd.DataFrame, items: pd.DataFrame) -> AnalyticalBundle:
    """Constrói todas as bases consumidas pelo dashboard."""

    validate_required_columns(nf, REQUIRED_NF_COLUMNS, "NF")
    validate_required_columns(items, REQUIRED_ITEM_COLUMNS, "NFITEM")
    validate_source_structure(nf, items)

    valid_nf = nf.loc[nf["TP_SITUACAO"].eq("E")].copy()
    header = valid_nf[[*JOIN_KEY, *HEADER_ATTRIBUTES]].copy()

    try:
        integrated = items.merge(
            header,
            on=JOIN_KEY,
            how="inner",
            validate="many_to_one",
        )
    except MergeError as exc:
        raise CardinalityError(
            f"Merge NFITEM→NF violou relação many_to_one na chave {JOIN_KEY}: {exc}"
        ) from exc

    item_header_match = items.merge(
        valid_nf[JOIN_KEY],
        on=JOIN_KEY,
        how="left",
        indicator=True,
        validate="many_to_one",
    )
    unmatched_items = item_header_match.loc[
        item_header_match["_merge"].eq("left_only")
    ].drop(columns="_merge")

    expected_flow = integrated["TP_OPERACAO"].map({"E": "ENTRADA", "S": "SAIDA"})
    flow_issues = integrated.loc[
        expected_flow.isna() | expected_flow.ne(integrated["CFOP_TIPO_FLUXO"])
    ].copy()

    is_sale = integrated["CFOP_TIPO_OPERACAO"].isin(SALES_OPERATIONS)
    is_valid_return = (
        integrated["CFOP_TIPO_OPERACAO"].eq(RETURN_OPERATION)
        & integrated["CFOP_TIPO_FLUXO"].eq("ENTRADA")
        & integrated["TIPO_ITEM_FISCAL"].eq("PRODUTO")
    )
    integrated["CLASSIFICACAO_RECEITA"] = np.select(
        [is_sale, is_valid_return],
        ["VENDA", "DEVOLUCAO"],
        default="EXCLUIDA",
    )
    integrated["MOTIVO_EXCLUSAO"] = integrated["CFOP_TIPO_OPERACAO"].fillna(
        "OPERACAO AUSENTE"
    )

    sales = integrated.loc[integrated["CLASSIFICACAO_RECEITA"].eq("VENDA")].copy()
    returns = integrated.loc[
        integrated["CLASSIFICACAO_RECEITA"].eq("DEVOLUCAO")
    ].copy()
    excluded = integrated.loc[
        integrated["CLASSIFICACAO_RECEITA"].eq("EXCLUIDA")
    ].copy()

    quality = _build_quality(
        nf,
        items,
        valid_nf,
        integrated,
        unmatched_items,
        flow_issues,
    )

    return AnalyticalBundle(
        nf=nf,
        items=items,
        valid_nf=valid_nf,
        integrated=integrated,
        sales=sales,
        returns=returns,
        excluded=excluded,
        unmatched_items=unmatched_items,
        flow_issues=flow_issues,
        quality=quality,
    )
