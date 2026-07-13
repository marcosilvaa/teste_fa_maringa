from __future__ import annotations

import argparse
from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "notebooks" / "faturamento.ipynb"


def md(text: str):
    return new_markdown_cell(text.strip())


def code(text: str):
    return new_code_cell(text.strip())


def build_notebook():
    cells = [
        md("""
# 1. Análise principal de faturamento

## Objetivo

Construir a base analítica principal para responder às métricas de faturamento com rastreabilidade e consistência.

Este notebook parte das premissas validadas na análise exploratória anterior. Não executa nova EDA ampla. O foco é consolidar faturamento bruto, preparar a validação do faturamento líquido, integrar os itens e estruturar métricas futuras.

**Perguntas de negócio:** faturamento bruto e líquido, descontos, quantidade faturada, quantidade de notas, ticket médio, evolução diária, empresa e principais produtos.
"""),
        md("""
# 2. Premissas consolidadas

- `DT_FATURA` é a data principal do relatório.
- `TP_SITUACAO = 'E'` representa o universo válido.
- A base candidata ao faturamento bruto usa `TP_SITUACAO = 'E'` e `TP_OPERACAO = 'S'`.
- `TP_MODDCTOFISCAL = 55` é o modelo fiscal relevante dentro desse subconjunto; outros modelos permanecem visíveis até validação.
- `VL_TOTALNOTA` é a melhor candidata ao valor final da nota.
- `NR_NF + CD_SERIE` não é chave perfeita na base completa, mas não apresentou duplicidade no subconjunto candidato.
- `NR_NF + CD_SERIE + TP_MODDCTOFISCAL` também não apresentou duplicidade no subconjunto candidato.
- As dimensões de empresa existem, mas possuem valor único no recorte atual.
- `CD_OPERACAO` apoiará a investigação de devoluções sem classificação semântica prematura.
- Faturamento líquido, devoluções e ligação com `NFITEM` continuam pendentes de validação.
"""),
        code("""
PREMISSAS = {
    "campo_data_principal": "DT_FATURA",
    "situacao_valida": "E",
    "operacao_saida": "S",
    "modelo_fiscal_relevante": 55,
    "campo_valor_nota_candidato": "VL_TOTALNOTA",
}

PREMISSAS
"""),
        md("""
# 3. Imports e configurações

Configuração mínima para tratamento, validações e gráficos analíticos simples. O notebook não possui finalidade de dashboard.
"""),
        code("""
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

pd.set_option("display.max_columns", 100)
pd.set_option("display.max_rows", 100)
pd.set_option("display.float_format", lambda valor: f"{valor:,.2f}")

sns.set_theme(style="whitegrid")
plt.rcParams["figure.figsize"] = (12, 5)
plt.rcParams["axes.titlesize"] = 12
"""),
        md("""
# 4. Carregamento dos dados

Arquivos de referência: `data/NF.csv` e `data/NFITEM.csv`. Ajustar diretório, nomes, separador ou codificação caso o ambiente futuro seja diferente.
"""),
        code("""
# Ajustar estes caminhos quando os arquivos forem movidos ou renomeados.
# Os candidatos permitem executar pela raiz do projeto ou pela pasta notebooks/.
DIRETORIOS_CANDIDATOS = [Path("data"), Path("../data")]
DIRETORIO_DADOS = next(
    (diretorio for diretorio in DIRETORIOS_CANDIDATOS if diretorio.exists()),
    DIRETORIOS_CANDIDATOS[0],
)
CAMINHO_NF = DIRETORIO_DADOS / "NF.csv"
CAMINHO_NFITEM = DIRETORIO_DADOS / "NFITEM.csv"

for caminho in [CAMINHO_NF, CAMINHO_NFITEM]:
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho.resolve()}")

df_nf = pd.read_csv(CAMINHO_NF, encoding="utf-8-sig", low_memory=False)
df_nfitem = pd.read_csv(CAMINHO_NFITEM, encoding="utf-8-sig", low_memory=False)

# Remove índices técnicos criados por exportações anteriores.
df_nf = df_nf.loc[:, ~df_nf.columns.str.match(r"^Unnamed")]
df_nfitem = df_nfitem.loc[:, ~df_nfitem.columns.str.match(r"^Unnamed")]

print(f"NF: {df_nf.shape[0]:,} linhas x {df_nf.shape[1]} colunas")
print(f"NFITEM: {df_nfitem.shape[0]:,} linhas x {df_nfitem.shape[1]} colunas")
"""),
        md("""
# 5. Validações iniciais mínimas

Validar estrutura, tipos essenciais e nulidade em campos críticos antes dos cálculos. Estas verificações não repetem a EDA anterior.
"""),
        code("""
COLUNAS_ESPERADAS_NF = [
    "CD_EMPRESA", "NR_FATURA", "DT_FATURA", "NR_NF", "CD_SERIE",
    "TP_MODDCTOFISCAL", "TP_OPERACAO", "TP_SITUACAO", "CD_OPERACAO",
    "QT_FATURADO", "VL_TOTALPRODUTO", "VL_DESCONTO", "VL_TOTALNOTA",
]
COLUNAS_ESPERADAS_NFITEM = [
    "CD_EMPRESA", "NR_FATURA", "DT_FATURA", "NR_ITEM", "CD_PRODUTO",
    "DS_PRODUTO", "QT_FATURADO", "VL_TOTALBRUTO", "VL_TOTALDESC",
    "VL_TOTALLIQUIDO",
]

def validar_colunas(df, colunas_esperadas, nome_base):
    ausentes = sorted(set(colunas_esperadas) - set(df.columns))
    if ausentes:
        raise KeyError(f"{nome_base}: colunas ausentes: {ausentes}")
    print(f"{nome_base}: colunas esperadas presentes.")

validar_colunas(df_nf, COLUNAS_ESPERADAS_NF, "NF")
validar_colunas(df_nfitem, COLUNAS_ESPERADAS_NFITEM, "NFITEM")
"""),
        code("""
COLUNAS_DATA_NF = ["DT_FATURA", "DT_EMISSAO", "DT_CADASTRO", "DT_SAIDAENTRADA"]
COLUNAS_NUMERICAS_NF = [
    "NR_NF", "CD_SERIE", "TP_MODDCTOFISCAL", "QT_FATURADO",
    "VL_TOTALPRODUTO", "VL_DESCONTO", "VL_TOTALNOTA",
]
COLUNAS_DATA_NFITEM = ["DT_FATURA", "DT_CADASTRO"]
COLUNAS_NUMERICAS_NFITEM = [
    "NR_ITEM", "CD_PRODUTO", "QT_FATURADO", "VL_TOTALBRUTO",
    "VL_TOTALDESC", "VL_TOTALLIQUIDO",
]

for coluna in COLUNAS_DATA_NF:
    if coluna in df_nf:
        df_nf[coluna] = pd.to_datetime(df_nf[coluna], errors="coerce", dayfirst=True)
for coluna in COLUNAS_NUMERICAS_NF:
    if coluna in df_nf:
        df_nf[coluna] = pd.to_numeric(df_nf[coluna], errors="coerce")
for coluna in COLUNAS_DATA_NFITEM:
    if coluna in df_nfitem:
        df_nfitem[coluna] = pd.to_datetime(df_nfitem[coluna], errors="coerce", dayfirst=True)
for coluna in COLUNAS_NUMERICAS_NFITEM:
    if coluna in df_nfitem:
        df_nfitem[coluna] = pd.to_numeric(df_nfitem[coluna], errors="coerce")

CAMPOS_CRITICOS_NF = [
    "DT_FATURA", "NR_NF", "CD_SERIE", "TP_SITUACAO", "TP_OPERACAO",
    "TP_MODDCTOFISCAL", "VL_TOTALNOTA",
]
CAMPOS_CRITICOS_NFITEM = [
    "CD_EMPRESA", "NR_FATURA", "NR_ITEM", "CD_PRODUTO", "QT_FATURADO",
]

validacao_inicial = {
    "shape_nf": df_nf.shape,
    "shape_nfitem": df_nfitem.shape,
    "tipos_nf": df_nf[CAMPOS_CRITICOS_NF].dtypes.astype(str).to_dict(),
    "tipos_nfitem": df_nfitem[CAMPOS_CRITICOS_NFITEM].dtypes.astype(str).to_dict(),
    "nulos_nf": df_nf[CAMPOS_CRITICOS_NF].isna().sum().to_dict(),
    "nulos_nfitem": df_nfitem[CAMPOS_CRITICOS_NFITEM].isna().sum().to_dict(),
}
validacao_inicial
"""),
        md("""
# 6. Construção da base candidata ao faturamento bruto

Aplicar somente filtros consolidados: situação válida `E` e operação de saída `S`. O modelo 55 será validado dentro do subconjunto; outros modelos ainda não serão removidos.
"""),
        code("""
mascara_faturamento_bruto = (
    df_nf["TP_SITUACAO"].eq(PREMISSAS["situacao_valida"])
    & df_nf["TP_OPERACAO"].eq(PREMISSAS["operacao_saida"])
)

df_fat_bruto = df_nf.loc[mascara_faturamento_bruto].copy()
df_fat_bruto["DT_FATURA_DIA"] = df_fat_bruto["DT_FATURA"].dt.normalize()

print(f"NF completa: {len(df_nf):,} linhas")
print(f"Candidatas ao faturamento bruto: {len(df_fat_bruto):,} linhas")
"""),
        md("""
# 7. Validação da base de faturamento bruto

Validar valores, chaves e distribuições relevantes. Divergências devem ser investigadas antes da consolidação definitiva.
"""),
        code("""
CHAVE_NOTA = ["NR_NF", "CD_SERIE"]
CHAVE_NOTA_MODELO = ["NR_NF", "CD_SERIE", "TP_MODDCTOFISCAL"]

duplicidades_chave_nota = df_fat_bruto.loc[
    df_fat_bruto.duplicated(CHAVE_NOTA, keep=False)
].sort_values(CHAVE_NOTA)
duplicidades_chave_nota_modelo = df_fat_bruto.loc[
    df_fat_bruto.duplicated(CHAVE_NOTA_MODELO, keep=False)
].sort_values(CHAVE_NOTA_MODELO)

resumo_fat_bruto = pd.Series({
    "quantidade_linhas": len(df_fat_bruto),
    "soma_vl_totalnota": df_fat_bruto["VL_TOTALNOTA"].sum(min_count=1),
    "soma_vl_totalproduto": df_fat_bruto["VL_TOTALPRODUTO"].sum(min_count=1),
    "nr_nf_cd_serie_unica": duplicidades_chave_nota.empty,
    "nr_nf_cd_serie_modelo_unica": duplicidades_chave_nota_modelo.empty,
})
resumo_fat_bruto
"""),
        code("""
distribuicao_modelo_fiscal = (
    df_fat_bruto.groupby("TP_MODDCTOFISCAL", dropna=False)
    .agg(
        QUANTIDADE_LINHAS=("NR_NF", "size"),
        QUANTIDADE_NOTAS=("NR_NF", "nunique"),
        FATURAMENTO_BRUTO=("VL_TOTALNOTA", "sum"),
    )
    .sort_values("FATURAMENTO_BRUTO", ascending=False)
)
distribuicao_modelo_fiscal
"""),
        code("""
distribuicao_operacao = (
    df_fat_bruto.groupby("CD_OPERACAO", dropna=False)
    .agg(
        QUANTIDADE_LINHAS=("NR_NF", "size"),
        QUANTIDADE_NOTAS=("NR_NF", "nunique"),
        FATURAMENTO_BRUTO=("VL_TOTALNOTA", "sum"),
    )
    .sort_values("FATURAMENTO_BRUTO", ascending=False)
)
distribuicao_operacao
"""),
        md("""
## Cautela sobre `CD_OPERACAO`

`CD_OPERACAO` permanecerá disponível para investigação de devoluções e exceções. Nenhum código será classificado como venda, devolução ou ajuste sem evidência adicional.
"""),
        md("""
# 8. Preparação para definição de faturamento líquido

A regra permanece em aberto. Devem ser investigadas devoluções, entradas válidas relacionadas, vínculos com documentos originais, significado de `CD_OPERACAO`, descontos e critérios de abatimento.
"""),
        code("""
# PLACEHOLDERS — preencher somente após validação de negócio.
CODIGOS_OPERACAO_DEVOLUCAO = []
CRITERIOS_ENTRADA_DEVOLUCAO = {}
CAMPO_DESCONTO_VALIDADO = None
REGRA_FATURAMENTO_LIQUIDO_VALIDADA = False

df_candidatos_devolucao = df_nf.iloc[0:0].copy()
df_entradas_associadas_devolucao = df_nf.iloc[0:0].copy()

print("Faturamento líquido: regra ainda pendente de validação.")
"""),
        md("""
# 9. Métricas por nota

Usar o mesmo escopo de `df_fat_bruto` para manter coerência entre faturamento, quantidade de notas e ticket médio.
"""),
        code("""
df_metricas_nota = (
    df_fat_bruto.groupby(CHAVE_NOTA, as_index=False, dropna=False)
    .agg(
        DT_FATURA=("DT_FATURA", "min"),
        CD_EMPRESA=("CD_EMPRESA", "first"),
        TP_MODDCTOFISCAL=("TP_MODDCTOFISCAL", "first"),
        CD_OPERACAO=("CD_OPERACAO", "first"),
        TOTAL_BRUTO_NOTA=("VL_TOTALNOTA", "sum"),
        TOTAL_PRODUTO_NOTA=("VL_TOTALPRODUTO", "sum"),
    )
)

quantidade_notas_distintas = len(df_metricas_nota)
faturamento_bruto_total = df_metricas_nota["TOTAL_BRUTO_NOTA"].sum()
ticket_medio_nota = (
    faturamento_bruto_total / quantidade_notas_distintas
    if quantidade_notas_distintas else np.nan
)

pd.Series({
    "faturamento_bruto": faturamento_bruto_total,
    "quantidade_notas_distintas": quantidade_notas_distintas,
    "ticket_medio_nota": ticket_medio_nota,
})
"""),
        md("""
# 10. Análise temporal

Agregar métricas por `DT_FATURA`, data oficial do relatório, preparando evolução diária, volume de notas e ticket médio diário.
"""),
        code("""
df_fat_diario = (
    df_metricas_nota.assign(DT_FATURA=lambda df: df["DT_FATURA"].dt.normalize())
    .groupby("DT_FATURA", as_index=False)
    .agg(
        FATURAMENTO_BRUTO=("TOTAL_BRUTO_NOTA", "sum"),
        QUANTIDADE_NOTAS=("NR_NF", "size"),
    )
    .sort_values("DT_FATURA")
)
df_fat_diario["TICKET_MEDIO_DIARIO"] = (
    df_fat_diario["FATURAMENTO_BRUTO"] / df_fat_diario["QUANTIDADE_NOTAS"]
)
df_fat_diario.head()
"""),
        code("""
fig, ax = plt.subplots()
sns.lineplot(data=df_fat_diario, x="DT_FATURA", y="FATURAMENTO_BRUTO", marker="o", ax=ax)
ax.set(
    title="Evolução diária do faturamento bruto",
    xlabel="Data de faturamento",
    ylabel="Faturamento bruto",
)
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
"""),
        md("""
# 11. Empresa

A dimensão empresa existe, mas aparenta possuir valor único no recorte atual. O agrupamento fica preparado para bases futuras, sem criar segmentação artificial.
"""),
        code("""
COLUNAS_EMPRESA = [
    coluna for coluna in ["CD_EMPRESA", "CD_EMPFAT", "CD_GRUPOEMPRESA"]
    if coluna in df_fat_bruto.columns
]
cardinalidade_empresa = df_fat_bruto[COLUNAS_EMPRESA].nunique(dropna=False)

df_fat_empresa = (
    df_fat_bruto.groupby("CD_EMPRESA", as_index=False, dropna=False)
    .agg(
        FATURAMENTO_BRUTO=("VL_TOTALNOTA", "sum"),
        QUANTIDADE_NOTAS=("NR_NF", "nunique"),
    )
)

if df_fat_empresa["CD_EMPRESA"].nunique(dropna=False) <= 1:
    print("Recorte atual possui uma empresa; nenhuma segmentação adicional será criada.")

cardinalidade_empresa, df_fat_empresa
"""),
        md("""
# 12. Integração com NFITEM

Quantidade faturada e rankings de produtos dependem de `NFITEM`. No esquema atual, `NFITEM` possui `CD_PRODUTO` e `DS_PRODUTO`, mas não possui `NR_NF` nem `CD_SERIE`.

`CD_EMPRESA + NR_FATURA` será tratada somente como chave candidata. **Não somar `VL_TOTALNOTA` após juntar cabeçalho com itens**, pois o valor da nota seria replicado uma vez por item. Métricas de produto devem usar valores do item.
"""),
        code("""
# PLACEHOLDER: confirmar esta chave com documentação do sistema de origem.
CHAVE_JUNCAO_CANDIDATA = ["CD_EMPRESA", "NR_FATURA"]

chaves_fat_bruto = df_fat_bruto[CHAVE_JUNCAO_CANDIDATA].drop_duplicates()

df_nfitem_fat_bruto = df_nfitem.merge(
    chaves_fat_bruto,
    on=CHAVE_JUNCAO_CANDIDATA,
    how="inner",
    validate="many_to_one",
)

cobertura_integracao = chaves_fat_bruto.merge(
    df_nfitem[CHAVE_JUNCAO_CANDIDATA].drop_duplicates(),
    on=CHAVE_JUNCAO_CANDIDATA,
    how="left",
    indicator=True,
    validate="one_to_one",
)

validacao_integracao = pd.Series({
    "linhas_nfitem_original": len(df_nfitem),
    "linhas_nfitem_filtrado": len(df_nfitem_fat_bruto),
    "notas_candidatas": len(chaves_fat_bruto),
    "notas_sem_item": cobertura_integracao["_merge"].eq("left_only").sum(),
})
validacao_integracao
"""),
        code("""
# Agregações preliminares. Dependem da validação da chave e das regras finais.
df_produto = (
    df_nfitem_fat_bruto.groupby(["CD_PRODUTO", "DS_PRODUTO"], as_index=False, dropna=False)
    .agg(
        QUANTIDADE_FATURADA=("QT_FATURADO", "sum"),
        FATURAMENTO_BRUTO_ITEM=("VL_TOTALBRUTO", "sum"),
        DESCONTO_ITEM=("VL_TOTALDESC", "sum"),
        FATURAMENTO_LIQUIDO_ITEM=("VL_TOTALLIQUIDO", "sum"),
    )
)

principais_produtos_faturamento = df_produto.nlargest(10, "FATURAMENTO_BRUTO_ITEM")
principais_produtos_quantidade = df_produto.nlargest(10, "QUANTIDADE_FATURADA")

CHAVE_JUNCAO_VALIDADA = False
print("Chave NF x NFITEM ainda pendente de validação.")
"""),
        md("""
# 13. Checklist de pendências analíticas

- [ ] Consolidar regra final de faturamento bruto e tratamento de modelos diferentes de 55.
- [ ] Definir regra final de faturamento líquido.
- [ ] Definir tratamento definitivo de devoluções e uso de `CD_OPERACAO`.
- [ ] Confirmar chave definitiva entre NF e NFITEM.
- [ ] Definir quantidade faturada oficial.
- [ ] Confirmar `CD_PRODUTO` e `DS_PRODUTO` como campos principais de produto.
- [ ] Confirmar uso de `VL_TOTALNOTA` e `VL_TOTALPRODUTO`.
- [ ] Confirmar campos de desconto no cabeçalho e nos itens.
- [ ] Reconciliar valores do cabeçalho com valores dos itens.
"""),
        code("""
pendencias_analiticas = pd.DataFrame(
    [
        ("Regra final de faturamento bruto", "Em validação"),
        ("Regra final de faturamento líquido", "Pendente"),
        ("Tratamento de devoluções", "Pendente"),
        ("Classificação de CD_OPERACAO", "Pendente"),
        ("Chave NF x NFITEM", "Pendente"),
        ("Definição de quantidade faturada", "Pendente"),
        ("Campo principal de produto", "Pendente"),
        ("Campo de desconto", "Pendente"),
        ("Reconciliação cabeçalho x itens", "Pendente"),
    ],
    columns=["PENDENCIA", "STATUS"],
)
pendencias_analiticas
"""),
        md("""
# 14. Próximos passos

1. Consolidar e reconciliar o faturamento bruto.
2. Validar o faturamento líquido e o tratamento de devoluções.
3. Confirmar a integração com `NFITEM`.
4. Validar quantidade e valores por produto.
5. Construir os outputs finais somente após aprovação das regras.

Este notebook termina como base analítica incremental. Seus resultados não constituem relatório final enquanto o checklist permanecer aberto.
"""),
    ]

    notebook = new_notebook(
        cells=cells,
        metadata={
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3"},
        },
    )
    return notebook


def validate_notebook(notebook) -> None:
    nbformat.validate(notebook)
    markdown = "\n".join(
        cell.source for cell in notebook.cells if cell.cell_type == "markdown"
    )
    source = "\n".join(cell.source for cell in notebook.cells)

    expected_titles = [
        "# 1. Análise principal de faturamento",
        "# 2. Premissas consolidadas",
        "# 3. Imports e configurações",
        "# 4. Carregamento dos dados",
        "# 5. Validações iniciais mínimas",
        "# 6. Construção da base candidata ao faturamento bruto",
        "# 7. Validação da base de faturamento bruto",
        "# 8. Preparação para definição de faturamento líquido",
        "# 9. Métricas por nota",
        "# 10. Análise temporal",
        "# 11. Empresa",
        "# 12. Integração com NFITEM",
        "# 13. Checklist de pendências analíticas",
        "# 14. Próximos passos",
    ]
    positions = [markdown.index(title) for title in expected_titles]
    assert positions == sorted(positions), "Seções ausentes ou fora de ordem"

    required_terms = [
        "df_nf", "df_nfitem", "df_fat_bruto", "df_fat_diario",
        "df_metricas_nota", "DT_FATURA", "TP_SITUACAO", "TP_OPERACAO",
        "TP_MODDCTOFISCAL", "VL_TOTALNOTA", "VL_TOTALPRODUTO", "NR_NF",
        "CD_SERIE", "CD_OPERACAO", "CD_PRODUTO", "DS_PRODUTO",
    ]
    missing = [term for term in required_terms if term not in source]
    assert not missing, f"Termos obrigatórios ausentes: {missing}"

    for cell in notebook.cells:
        if cell.cell_type == "code":
            assert cell.execution_count is None
            assert not cell.outputs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()

    if args.validate_only:
        if not OUTPUT.exists():
            raise FileNotFoundError(OUTPUT)
        notebook = nbformat.read(OUTPUT, as_version=4)
        validate_notebook(notebook)
        print(f"Notebook válido e sem outputs: {OUTPUT}")
        return

    notebook = build_notebook()
    validate_notebook(notebook)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(notebook, OUTPUT)
    print(f"Notebook criado: {OUTPUT}")


if __name__ == "__main__":
    main()
