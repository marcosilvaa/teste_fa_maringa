from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]
PAGES = [
    ROOT / "app.py",
    ROOT / "pages" / "01_Visao_Geral.py",
    ROOT / "pages" / "03_Produtos.py",
    ROOT / "pages" / "04_Devolucoes.py",
    ROOT / "pages" / "05_Empresas_Operacoes.py",
    ROOT / "pages" / "06_Metodologia_Qualidade.py",
]


@pytest.mark.parametrize("page", PAGES, ids=lambda path: path.stem)
def test_page_runs_without_streamlit_exception(page: Path):
    app = AppTest.from_file(str(page), default_timeout=120).run()
    assert not app.exception, [exception.message for exception in app.exception]
