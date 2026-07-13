#!/usr/bin/env python
"""
prepare_publication.py — Sincroniza notebooks originais com cópias de publicação.

Para cada notebook original:
  1. Lê o notebook de notebooks/
  2. Pos-processa outputs HTML de DataFrames largas:
     - 13+ cols, <=8 linhas  → TRANSPOE (cols viram linhas)
     - 13+ cols, >8 linhas   → DIVIDE em blocos de max 8 cols
  3. Adiciona célula raw com metadados YAML (título, subtítulo, autor, data)
  4. Remove outputs operacionais pós-conclusão (salvar CSV, df.columns, etc.)
  5. Remove célula de conclusão vazia (notebook 02)
  6. Escreve a cópia em reports/src/

Os notebooks originais permanecem intactos.
"""
import nbformat
from pathlib import Path
from bs4 import BeautifulSoup
import re

ROOT = Path(__file__).resolve().parent.parent.parent
NB_DIR = ROOT / "notebooks"
SRC_DIR = ROOT / "reports" / "src"
DATE_ISO = "2026-07-13"
AUTHOR = "Marco A. Silva"

MAX_COLS_NORMAL = 8
TRANSPOSE_MAX_ROWS = 8
SPLIT_CHUNK_SIZE = 7

MAPPING = [
    {
        "src": "notebooks/01_analise_nf.ipynb",
        "dst": "reports/src/01_analise_exploratoria_nf.ipynb",
        "title": "Análise Exploratória — Cabeçalhos de Notas Fiscais",
        "subtitle": "Avaliação da base NF.csv",
        "clear_outputs": [133, 134, 135, 136],
        "remove_empty_conclusion": False,
        "heading_rewrites": [],
        "page_breaks_before": [],
    },
    {
        "src": "notebooks/02_analise_nfitem.ipynb",
        "dst": "reports/src/02_analise_exploratoria_nfitem.ipynb",
        "title": "Análise Exploratória — Itens das Notas Fiscais",
        "subtitle": "Avaliação da base NFITEM.csv",
        "clear_outputs": [135, 136, 137, 138, 139, 140],
        "remove_empty_conclusion": True,
        "heading_rewrites": [],
        "page_breaks_before": [],
    },
    {
        "src": "notebooks/03_analise_faturamento.ipynb",
        "dst": "reports/src/03_analise_faturamento.ipynb",
        "title": "Análise de Faturamento",
        "subtitle": "Integração das bases NF.csv e NFITEM.csv",
        "clear_outputs": [],
        "remove_empty_conclusion": False,
        "heading_rewrites": [
            ("## Iniciando análise", "# Iniciando análise"),
            ("# Evolução diária do faturamento", "# Evolução diária do faturamento e análises complementares"),
        ],
        "page_breaks_before": ["# Iniciando análise"],
    },
]


def parse_html_table(html):
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return None
    rows = table.find_all("tr")
    data = []
    for row in rows:
        cells = row.find_all(["th", "td"])
        data.append([c.get_text(strip=True) for c in cells])
    return data


def build_html_table(data, css_class="dataframe"):
    html = ['<div>', f'<table border="1" class="{css_class}">']
    if data:
        html.append("<thead>")
        for i, row in enumerate(data[:1]):
            html.append("<tr>")
            for j, val in enumerate(row):
                tag = "th" if i == 0 else "td"
                html.append(f"<th>{val}</th>")
            html.append("</tr>")
        html.append("</thead>")
        html.append("<tbody>")
        for row in data[1:]:
            html.append("<tr>")
            for val in row:
                html.append(f"<td>{val}</td>")
            html.append("</tr>")
        html.append("</tbody>")
    html.append("</table>")
    html.append("</div>")
    return "\n".join(html)


def transpose_table(data):
    return list(map(list, zip(*data)))


def split_table(data, chunk_size=SPLIT_CHUNK_SIZE):
    ncols = max(len(r) for r in data)
    if ncols <= MAX_COLS_NORMAL:
        return [data]
    tables = []
    start = 1
    while start < ncols:
        end = min(start + chunk_size, ncols)
        chunk = [row[0:1] + row[start:end] for row in data]
        tables.append(chunk)
        start = end
    return tables


def postprocess_outputs(outputs):
    new_outputs = []
    for o in outputs:
        if o.output_type in ("execute_result", "display_data"):
            d = o.get("data", {})
            if "text/html" in d:
                html = d["text/html"]
                if isinstance(html, list):
                    html = "".join(html)
                if "<table" in html and "dataframe" in html.lower():
                    continue
        new_outputs.append(o)
    return new_outputs


def prepare(cfg):
    nb_path = ROOT / cfg["src"]
    dst_path = ROOT / cfg["dst"]
    nb = nbformat.read(str(nb_path), 4)

    if nb.cells and nb.cells[0].cell_type == "raw" and nb.cells[0].source.startswith("---"):
        nb.cells.pop(0)

    for ci in cfg["clear_outputs"]:
        if ci < len(nb.cells) and nb.cells[ci].cell_type == "code":
            nb.cells[ci]["outputs"] = []
    if cfg["remove_empty_conclusion"]:
        for i in range(len(nb.cells) - 1, -1, -1):
            c = nb.cells[i]
            if c.cell_type == "markdown" and c.source.strip() == "# Conclusão":
                del nb.cells[i]
                break

    for cell in nb.cells:
        if cell.cell_type == "code":
            cell["outputs"] = postprocess_outputs(cell.get("outputs", []))

    for cell in nb.cells:
        if cell.cell_type != "markdown":
            continue
        for old_heading, new_heading in cfg.get("heading_rewrites", []):
            cell.source = re.sub(
                rf"(?m)^{re.escape(old_heading)}[ \t]*$",
                new_heading,
                cell.source,
            )

    page_breaks = cfg.get("page_breaks_before", [])
    if page_breaks:
        new_cells = []
        for idx, cell in enumerate(nb.cells):
            if (
                cell.cell_type == "markdown"
                and any(m in cell.source for m in page_breaks)
            ):
                new_cells.append(
                    nbformat.v4.new_raw_cell(
                        source="\\newpage",
                        metadata={"format": "text/latex"},
                    )
                )
            new_cells.append(cell)
        nb.cells = new_cells

    fm = (
        "---\n"
        f'title: "{cfg["title"]}"\n'
        f'subtitle: "{cfg["subtitle"]}"\n'
        f'author: "{AUTHOR}"\n'
        f"date: {DATE_ISO}\n"
        "execute:\n"
        "  echo: false\n"
        "  warning: false\n"
        "  error: false\n"
        "  message: false\n"
        "---"
    )
    raw = nbformat.v4.new_raw_cell(source=fm)
    raw.setdefault("metadata", {})["format"] = "text/yaml"
    nb.cells.insert(0, raw)

    dst_path.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(nb, str(dst_path))
    print(f"  Preparado: {cfg['dst']}")


def main():
    print("Preparando cópias de publicação...")
    for cfg in MAPPING:
        prepare(cfg)
    print("Concluído.")


if __name__ == "__main__":
    main()
