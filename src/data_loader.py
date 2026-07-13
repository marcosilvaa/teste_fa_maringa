"""Leitura tipada e cache invalidável das fontes CSV."""

from __future__ import annotations

from pathlib import Path
from typing import TypeAlias

import pandas as pd
import streamlit as st

from src.exceptions import DataSourceError


SourceSignature: TypeAlias = tuple[tuple[str, int, int], ...]

NF_TEXT_COLUMNS = {
    "CD_EMPRESA": "string",
    "CD_EMPFAT": "string",
    "CD_GRUPOEMPRESA": "string",
    "NR_FATURA": "string",
    "CD_PESSOA": "string",
    "NR_NF": "string",
    "CD_SERIE": "string",
    "CD_OPERACAO": "string",
    "TP_OPERACAO": "string",
    "TP_SITUACAO": "string",
}

ITEM_TEXT_COLUMNS = {
    "CD_EMPRESA": "string",
    "CD_EMPFAT": "string",
    "CD_GRUPOEMPRESA": "string",
    "NR_FATURA": "string",
    "NR_ITEM": "string",
    "CD_CFOP": "string",
    "CD_CST": "string",
    "CD_TIPI": "string",
    "CD_PRODUTO": "string",
    "CD_ESPECIE": "string",
    "DS_PRODUTO": "string",
    "CFOP_TIPO_FLUXO": "string",
    "CFOP_CLASSE_GERAL": "string",
    "CFOP_TIPO_OPERACAO": "string",
    "TIPI_GRUPO_FISCAL": "string",
    "TIPI_FAMILIA_COMERCIAL": "string",
    "TIPO_ITEM_FISCAL": "string",
}


def source_signature(*paths: Path) -> SourceSignature:
    """Assina fontes por caminho, tamanho e modificação em nanossegundos."""

    signatures: list[tuple[str, int, int]] = []
    for path in paths:
        resolved = path.resolve()
        if not resolved.exists():
            raise DataSourceError(
                f"Arquivo obrigatório não encontrado: {resolved}. "
                "Configure FAMARINGA_DATA_DIR ou os caminhos individuais."
            )
        if not resolved.is_file():
            raise DataSourceError(f"Fonte configurada não é um arquivo: {resolved}")
        stat = resolved.stat()
        signatures.append((str(resolved), stat.st_size, stat.st_mtime_ns))
    return tuple(signatures)


def _normalize_nf(df: pd.DataFrame) -> pd.DataFrame:
    result = df.loc[:, ~df.columns.str.match(r"^Unnamed")].copy()
    for column in ["DT_FATURA", "DT_EMISSAO"]:
        if column in result:
            result[column] = pd.to_datetime(result[column], errors="coerce").dt.normalize()
    return result


def _normalize_items(df: pd.DataFrame) -> pd.DataFrame:
    result = df.loc[:, ~df.columns.str.match(r"^Unnamed")].copy()
    if "DT_FATURA" in result:
        result["DT_FATURA"] = pd.to_datetime(
            result["DT_FATURA"], errors="coerce"
        ).dt.normalize()
    for column in ["QT_FATURADO", "VL_TOTALBRUTO", "VL_TOTALDESC", "VL_TOTALLIQUIDO"]:
        if column in result:
            result[column] = pd.to_numeric(result[column], errors="coerce")
    return result


@st.cache_data(show_spinner=False)
def load_source_data(
    nf_path: str,
    item_path: str,
    signature: SourceSignature,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Lê fontes; `signature` participa da chave do cache."""

    del signature
    try:
        nf = pd.read_csv(
            nf_path,
            encoding="utf-8-sig",
            dtype=NF_TEXT_COLUMNS,
            low_memory=False,
        )
        items = pd.read_csv(
            item_path,
            encoding="utf-8-sig",
            dtype=ITEM_TEXT_COLUMNS,
            low_memory=False,
        )
    except (OSError, UnicodeError, pd.errors.ParserError) as exc:
        raise DataSourceError(f"Falha ao ler os CSVs: {exc}") from exc
    return _normalize_nf(nf), _normalize_items(items)


def load_sources(nf_path: Path, item_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Entrada pública com invalidação automática do cache."""

    signature = source_signature(nf_path, item_path)
    return load_source_data(str(nf_path.resolve()), str(item_path.resolve()), signature)
