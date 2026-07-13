# Relatórios F.A. Maringá

Renderização em PDF profissional dos notebooks analíticos de faturamento, via Quarto.

## Mapeamento notebook → PDF

| Notebook (original, intocado) | Cópia de publicação | PDF gerado |
|---|---|---|
| `notebooks/01_analise_nf.ipynb` | `reports/src/01_analise_exploratoria_nf.ipynb` | `reports/pdf/01_analise_exploratoria_nf.pdf` |
| `notebooks/02_analise_nfitem.ipynb` | `reports/src/02_analise_exploratoria_nfitem.ipynb` | `reports/pdf/02_analise_exploratoria_nfitem.pdf` |
| `notebooks/03_analise_faturamento.ipynb` | `reports/src/03_analise_faturamento.ipynb` | `reports/pdf/03_analise_faturamento.pdf` |

### Correspondência dos relatórios

1. **Análise Exploratória — Cabeçalhos de Notas Fiscais** (`01_*`) — avaliação da base `NF.csv`.
2. **Análise Exploratória — Itens das Notas Fiscais** (`02_*`) — avaliação da base `NFITEM.csv`.
3. **Análise de Faturamento** (`03_*`) — integração de `NF.csv` e `NFITEM.csv`.

## Política de não reexecução

Os PDFs são renderizados a partir dos **outputs já salvos** nos notebooks. O Quarto é configurado com `execute.enabled: false`, portanto **nenhuma célula é reexecutada** durante a publicação padrão. As cópias de publicação em `reports/src/` preservam integralmente células, cálculos e outputs dos originais, acrescentando apenas uma célula `raw` de metadados (título, subtítulo, autor, data) no topo.

## Como atualizar os PDFs após alterar um notebook original

O fluxo de renderização é **automático**: o script `render_reports.sh` sempre regenera as cópias de publicação a partir dos notebooks originais antes de renderizar. Portanto:

1. Edite o notebook original em `notebooks/` (execute as células no Jupyter para salvar os outputs).
2. Rode:

```bash
bash reports/scripts/render_reports.sh
```

O script executa automaticamente:
- `prepare_publication.py` — lê os notebooks originais, adiciona metadados, suprime outputs operacionais pós-conclusão e grava as cópias em `reports/src/`.
- `quarto render` — converte cada cópia em PDF usando os outputs salvos (**sem reexecutar**).

**Não é necessário editar manualmente** os arquivos em `reports/src/` — eles são regenerados a cada execução.

> Se o número de células mudar no notebook original (ex: adicionou células no final), ajuste os índices em `reports/scripts/prepare_publication.py` (`clear_outputs`, `remove_empty_conclusion`).

## Formatação de tabelas largas

Tabelas com muitas colunas (DataFrames) são tratadas pelo filtro Lua `reports/scripts/table_format.lua`:

| Nº de colunas | Formatação aplicada |
|---|---|
| 1–8 | Colunas com quebra de texto automática (`p{width}`), larguras iguais |
| 9–12 | Quebra de texto + fonte `\small` + espaçamento entre colunas reduzido |
| 13+ | Página em **paisagem** + fonte `\scriptsize` + espaçamento mínimo |

Todas as colunas são preservadas — nenhuma é truncada. O conteúdo das células quebra em múltiplas linhas quando necessário.

## Dependências

- [Quarto](https://quarto.org) ≥ 1.6 (`quarto --version`)
- Distribuição LaTeX: **TinyTeX** com engine **xelatex** (`quarto check`)
- Python 3 (apenas para o script `prepare_publication.py`, que usa o `.venv` do projeto)

## Renderização

```bash
bash reports/scripts/render_reports.sh
```

Os três PDFs são gravados em `reports/pdf/`.

## Forçar reexecução (apenas quando essencial)

A reexecução só é necessária se outputs analíticos essenciais estiverem ausentes e o ambiente + dados estiverem disponíveis. Nesse caso:

```bash
quarto render reports/src/03_analise_faturamento.ipynb --execute --to pdf --output-dir reports/pdf
```

> Importante: reexecutar exige o ambiente Python do projeto (`.venv`) com `jupyter`, `pandas`, `matplotlib`, `seaborn` e os dados em `notebooks/`. A reexecução deve ser explicitamente documentada.

## Estrutura

```
_quarto.yml                      # configuração global do projeto Quarto
reports/
  README.md                      # este arquivo
  src/                           # cópias de publicação (geradas automaticamente)
  pdf/                           # PDFs finais
  assets/header.tex             # cabeçalho LaTeX (português, tabelas, hifenização)
  scripts/
    render_reports.sh            # automação: prepara + renderiza os 3 PDFs
    prepare_publication.py       # sincroniza notebooks originais → cópias de publicação
    table_format.lua             # filtro Lua: quebra de texto + paisagem para tabelas largas
```

## Limitações e ajustes de publicação

- A numeração de seções preserva a hierarquia de cabeçalhos dos notebooks originais.
- **Relatório 2** (`02_*`): o notebook original possui uma célula Markdown `# Conclusão` sem texto. Como publicar um título vazio não é adequado, a cópia de publicação remove essa célula. O notebook original em `notebooks/` permanece intacto.
- **Relatórios 1 e 2**: as células de código puramente operacionais posteriores à conclusão (salvar CSV, `df.columns`, `nunique`, `shape`, checagens de depuração) têm seus outputs suprimidos na cópia de publicação. A análise e os notebooks originais não são afetados.
- Tabelas com 13+ colunas usam página em paisagem com fonte reduzida para evitar truncamento.
- Tabelas com 9–12 colunas usam fonte `\small` com colsep reduzido.
- Todas as tabelas têm quebra de texto habilitada nas células.