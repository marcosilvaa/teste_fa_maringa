"""Configuração, contratos de dados e identidade visual."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"

JOIN_KEY = ["CD_EMPRESA", "CD_EMPFAT", "NR_FATURA", "DT_FATURA"]
ITEM_KEY = [*JOIN_KEY, "NR_ITEM"]
INVOICE_KEY = ["CD_EMPFAT", "CD_SERIE", "NR_NF"]
OFFICIAL_DATE = "DT_EMISSAO"

SALES_OPERATIONS = (
    "VENDA",
    "VENDA CONSUMIDOR FINAL",
    "VENDA SEM TRANSITO",
)
RETURN_OPERATION = "DEVOLUCAO"

REQUIRED_NF_COLUMNS = {
    "CD_EMPRESA",
    "CD_EMPFAT",
    "CD_GRUPOEMPRESA",
    "NR_FATURA",
    "DT_FATURA",
    "DT_EMISSAO",
    "CD_PESSOA",
    "NR_NF",
    "CD_SERIE",
    "TP_OPERACAO",
    "TP_SITUACAO",
    "CD_OPERACAO",
}

REQUIRED_ITEM_COLUMNS = {
    "CD_EMPRESA",
    "CD_EMPFAT",
    "CD_GRUPOEMPRESA",
    "NR_FATURA",
    "DT_FATURA",
    "NR_ITEM",
    "CD_CFOP",
    "CD_PRODUTO",
    "CD_ESPECIE",
    "DS_PRODUTO",
    "QT_FATURADO",
    "VL_TOTALBRUTO",
    "VL_TOTALDESC",
    "VL_TOTALLIQUIDO",
    "CFOP_TIPO_FLUXO",
    "CFOP_CLASSE_GERAL",
    "CFOP_TIPO_OPERACAO",
    "TIPI_GRUPO_FISCAL",
    "TIPI_FAMILIA_COMERCIAL",
    "TIPO_ITEM_FISCAL",
}

MONETARY_COLUMNS = ["VL_TOTALBRUTO", "VL_TOTALDESC", "VL_TOTALLIQUIDO"]
QUANTITY_COLUMNS = ["QT_FATURADO"]

COLORS = {
    "navy": "#17324D",
    "gross": "#64748B",
    "net": "#16856B",
    "returns": "#B8473D",
    "discount": "#C78A2C",
    "risk": "#8F2D2D",
    "ink": "#243444",
    "muted": "#6B7A88",
    "paper": "#F6F3EC",
    "grid": "#DCE2E7",
}


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Caminhos e parâmetros estáveis da aplicação."""

    nf_path: Path
    item_path: Path
    currency_tolerance: float = 0.01


def get_config() -> AppConfig:
    """Resolve fontes por variáveis de ambiente ou diretório padrão."""

    data_dir = Path(os.getenv("FAMARINGA_DATA_DIR", DEFAULT_DATA_DIR)).expanduser()
    nf_path = Path(os.getenv("FAMARINGA_NF_PATH", data_dir / "NF.csv")).expanduser()
    item_path = Path(
        os.getenv("FAMARINGA_NFITEM_PATH", data_dir / "NFITEM.csv")
    ).expanduser()
    return AppConfig(nf_path=nf_path, item_path=item_path)
