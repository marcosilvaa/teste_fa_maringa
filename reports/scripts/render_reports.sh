#!/usr/bin/env bash
# render_reports.sh — renderiza os três relatórios PDF F.A. Maringá
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PDF_DIR="reports/pdf"
mkdir -p "$PDF_DIR"

note_prefix() { echo "[$(date +%H:%M:%S)] $*"; }

if ! command -v quarto >/dev/null 2>&1; then
  echo "ERRO: Quarto não encontrado no PATH." >&2
  exit 1
fi

note_prefix "Quarto: $(quarto --version)"
note_prefix "Verificando ambiente Quarto..."
quarto check >/tmp/quarto_check.log 2>&1 || { echo "AVISO: quarto check reportou problemas (ver /tmp/quarto_check.log)." >&2; }
quarto check jupyter >/tmp/quarto_check_jupyter.log 2>&1 || true

# Preparar cópias de publicação a partir dos notebooks originais
note_prefix "Preparando cópias de publicação..."
PYTHON="${ROOT}/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  PYTHON="python3"
fi
"$PYTHON" "${ROOT}/reports/scripts/prepare_publication.py"

notebooks=(
  "reports/src/01_analise_exploratoria_nf.ipynb"
  "reports/src/02_analise_exploratoria_nfitem.ipynb"
  "reports/src/03_analise_faturamento.ipynb"
)

for nb in "${notebooks[@]}"; do
  note_prefix "Renderizando: $nb"
  quarto render "$nb" --to pdf
done

# Quarto (project output-dir) espelha o caminho relativo do input.
# Achatar a saída para reports/pdf/<stem>.pdf.
nested="$PDF_DIR/reports/src"
if [[ -d "$nested" ]]; then
  for f in "$nested"/*.pdf; do
    [[ -f "$f" ]] && mv -f "$f" "$PDF_DIR/$(basename "$f")"
  done
  rm -rf "$nested"
fi

note_prefix "Verificando PDFs gerados..."
status=0
for nb in "${notebooks[@]}"; do
  stem="$(basename "$nb" .ipynb)"
  pdf="$PDF_DIR/${stem}.pdf"
  if [[ ! -f "$pdf" || ! -s "$pdf" ]]; then
    echo "ERRO: PDF ausente ou vazio: $pdf" >&2
    status=1
  else
    size=$(wc -c < "$pdf" | tr -d ' ')
    note_prefix "OK: $pdf (${size} bytes)"
  fi
done

exit $status