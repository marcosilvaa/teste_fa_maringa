from __future__ import annotations

import argparse
from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "notebooks" / "relatorio_faturamento.ipynb"


def md(source: str):
    return new_markdown_cell(source.strip())


def code(source: str):
    return new_code_cell(source.strip())


def build_notebook():
    cells = [
        md("""
# Relatório de faturamento comercial

## Objetivo

Apresentar métricas comerciais consolidadas e análises por tempo, empresa e produto, mantendo separação entre o grão da nota e o grão do item.

> **Status metodológico:** relatório provisório. Os filtros fiscais foram aprovados para esta análise, mas devoluções, CFOP e códigos de operação ainda exigem homologação antes da publicação oficial.
"""),
        md("""
## 1. Fontes, escopo e definições

**Fontes**

- `data/NF.csv`: cabeçalho de notas/faturas.
- `data/NFITEM.csv`: itens faturados.

**Escopo comercial provisório**

- `TP_SITUACAO = 'E'`.
- `TP_OPERACAO = 'S'`.
- Data oficial: `DT_FATURA`.
- Todos os modelos fiscais elegíveis permanecem no total; modelo 55 será evidenciado separadamente.

**Métricas**

- Faturamento bruto: soma de `NFITEM.VL_TOTALBRUTO` dos documentos elegíveis.
- Descontos: soma de `NFITEM.VL_TOTALDESC` no mesmo escopo.
- Faturamento líquido comercial provisório: soma de `NFITEM.VL_TOTALLIQUIDO`.
- Quantidade faturada: soma de `NFITEM.QT_FATURADO` por `CD_ESPECIE`; unidades incompatíveis não são somadas entre si.
- Notas distintas: chave `CD_EMPRESA + TP_MODDCTOFISCAL + CD_SERIE + NR_NF` no escopo elegível.
- Ticket médio: faturamento líquido dividido pelas notas distintas no mesmo escopo.
"""),
        code("""
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from IPython.display import display, Markdown

%matplotlib inline

pd.set_option("display.max_columns", 100)
pd.set_option("display.max_rows", 100)
pd.set_option("display.float_format", lambda x: f"{x:,.2f}")

sns.set_theme(style="whitegrid", palette="deep")
plt.rcParams.update({
    "figure.figsize": (12, 5),
    "axes.titlesize": 13,
    "axes.labelsize": 10,
})

FILTRO_SITUACAO = "E"
FILTRO_OPERACAO = "S"
MODELO_FISCAL_REFERENCIA = 55
TOLERANCIA_MONETARIA = 0.01
"""),
        md("""
## 2. Carregamento e validações mínimas

Localizar fontes tanto pela raiz do projeto quanto pela pasta `notebooks/`. CSVs permanecem intactos.
"""),
        code("""
DIRETORIOS_CANDIDATOS = [Path("data"), Path("../data")]
DIRETORIO_DADOS = next(
    (path for path in DIRETORIOS_CANDIDATOS if path.exists()),
    DIRETORIOS_CANDIDATOS[0],
)

CAMINHO_NF = DIRETORIO_DADOS / "NF.csv"
CAMINHO_NFITEM = DIRETORIO_DADOS / "NFITEM.csv"

for caminho in [CAMINHO_NF, CAMINHO_NFITEM]:
    if not caminho.exists():
        raise FileNotFoundError(f"Fonte não encontrada: {caminho.resolve()}")

df_nf = pd.read_csv(CAMINHO_NF, encoding="utf-8-sig", low_memory=False)
df_nfitem = pd.read_csv(CAMINHO_NFITEM, encoding="utf-8-sig", low_memory=False)

df_nf = df_nf.loc[:, ~df_nf.columns.str.match(r"^Unnamed")]
df_nfitem = df_nfitem.loc[:, ~df_nfitem.columns.str.match(r"^Unnamed")]

print(f"NF: {len(df_nf):,} linhas e {df_nf.shape[1]} colunas")
print(f"NFITEM: {len(df_nfitem):,} linhas e {df_nfitem.shape[1]} colunas")
"""),
        code("""
COLUNAS_NF = [
    "CD_EMPRESA", "NR_FATURA", "DT_FATURA", "NR_NF", "CD_SERIE",
    "TP_MODDCTOFISCAL", "TP_OPERACAO", "TP_SITUACAO", "CD_OPERACAO",
    "QT_FATURADO", "VL_TOTALPRODUTO", "VL_DESCONTO", "VL_TOTALNOTA",
]
COLUNAS_ITEM = [
    "CD_EMPRESA", "NR_FATURA", "NR_ITEM", "CD_PRODUTO", "DS_PRODUTO",
    "CD_ESPECIE", "QT_FATURADO", "VL_TOTALBRUTO", "VL_TOTALDESC",
    "VL_TOTALLIQUIDO",
]

def validar_colunas(df, esperadas, base):
    ausentes = sorted(set(esperadas) - set(df.columns))
    if ausentes:
        raise KeyError(f"{base}: colunas ausentes: {ausentes}")

validar_colunas(df_nf, COLUNAS_NF, "NF")
validar_colunas(df_nfitem, COLUNAS_ITEM, "NFITEM")

df_nf["DT_FATURA"] = pd.to_datetime(df_nf["DT_FATURA"], errors="coerce", dayfirst=True)

for coluna in [
    "VL_TOTALPRODUTO", "VL_DESCONTO", "VL_TOTALNOTA", "QT_FATURADO",
]:
    df_nf[coluna] = pd.to_numeric(df_nf[coluna], errors="coerce")

for coluna in [
    "VL_TOTALBRUTO", "VL_TOTALDESC", "VL_TOTALLIQUIDO", "QT_FATURADO",
]:
    df_nfitem[coluna] = pd.to_numeric(df_nfitem[coluna], errors="coerce")

campos_criticos_nf = [
    "CD_EMPRESA", "NR_FATURA", "DT_FATURA", "NR_NF", "CD_SERIE",
    "TP_MODDCTOFISCAL", "TP_OPERACAO", "TP_SITUACAO",
]
campos_criticos_item = [
    "CD_EMPRESA", "NR_FATURA", "NR_ITEM", "CD_PRODUTO", "CD_ESPECIE",
    "QT_FATURADO", "VL_TOTALBRUTO", "VL_TOTALDESC", "VL_TOTALLIQUIDO",
]

qualidade_inicial = pd.DataFrame({
    "base": ["NF", "NFITEM"],
    "linhas": [len(df_nf), len(df_nfitem)],
    "colunas": [df_nf.shape[1], df_nfitem.shape[1]],
    "nulos_campos_criticos": [
        int(df_nf[campos_criticos_nf].isna().sum().sum()),
        int(df_nfitem[campos_criticos_item].isna().sum().sum()),
    ],
})
display(qualidade_inicial)
"""),
        md("""
## 3. Chaves, granularidade e escopo elegível

Valores do cabeçalho não serão agregados depois do relacionamento 1:N. O cabeçalho define elegibilidade; os itens fornecem bruto, desconto, líquido, quantidade e produto.
"""),
        code("""
CHAVE_NOTA_INTERNA = ["CD_EMPRESA", "NR_FATURA"]
CHAVE_DOCUMENTO_FISCAL = [
    "CD_EMPRESA", "TP_MODDCTOFISCAL", "CD_SERIE", "NR_NF",
]
CHAVE_ITEM = CHAVE_NOTA_INTERNA + ["NR_ITEM"]

validacao_chaves = pd.DataFrame({
    "teste": [
        "Unicidade da nota interna no cabeçalho",
        "Unicidade do item",
        "Nulos na chave da nota",
        "Nulos na chave do item",
    ],
    "resultado": [
        not df_nf.duplicated(CHAVE_NOTA_INTERNA).any(),
        not df_nfitem.duplicated(CHAVE_ITEM).any(),
        not df_nf[CHAVE_NOTA_INTERNA].isna().any(axis=1).any(),
        not df_nfitem[CHAVE_ITEM].isna().any(axis=1).any(),
    ],
})
display(validacao_chaves)

if not validacao_chaves["resultado"].all():
    raise ValueError("Falha nas chaves técnicas; interromper cálculo oficial.")
"""),
        code("""
mascara_elegivel = (
    df_nf["TP_SITUACAO"].eq(FILTRO_SITUACAO)
    & df_nf["TP_OPERACAO"].eq(FILTRO_OPERACAO)
)
df_nf_elegivel = df_nf.loc[mascara_elegivel].copy()

atributos_elegiveis = df_nf_elegivel[
    CHAVE_NOTA_INTERNA + [
        "DT_FATURA", "NR_NF", "CD_SERIE", "TP_MODDCTOFISCAL",
        "CD_OPERACAO",
    ]
]

# DT_FATURA do cabeçalho é a referência oficial; evita sufixos _x/_y no merge.
df_item_elegivel = df_nfitem.drop(columns=["DT_FATURA"], errors="ignore").merge(
    atributos_elegiveis,
    on=CHAVE_NOTA_INTERNA,
    how="inner",
    validate="many_to_one",
)

cobertura = df_nf_elegivel[CHAVE_NOTA_INTERNA].merge(
    df_nfitem[CHAVE_NOTA_INTERNA].drop_duplicates(),
    on=CHAVE_NOTA_INTERNA,
    how="left",
    indicator=True,
    validate="one_to_one",
)

controle_escopo = pd.Series({
    "notas_base_completa": len(df_nf),
    "notas_elegiveis": len(df_nf_elegivel),
    "itens_base_completa": len(df_nfitem),
    "itens_elegiveis": len(df_item_elegivel),
    "notas_elegiveis_sem_item": int(cobertura["_merge"].eq("left_only").sum()),
})
display(controle_escopo.to_frame("valor"))
"""),
        md("""
## 4. Reconciliações e qualidade do relacionamento

Validar identidade `bruto − desconto = líquido` e reconciliar os totais dos itens com campos equivalentes do cabeçalho. Diferenças são exibidas; nenhuma divergência é ocultada.
"""),
        code("""
df_item_elegivel["DIF_BRUTO_DESC_LIQ"] = (
    df_item_elegivel["VL_TOTALBRUTO"]
    - df_item_elegivel["VL_TOTALDESC"]
    - df_item_elegivel["VL_TOTALLIQUIDO"]
)

reconciliacao_item = pd.Series({
    "linhas_fora_tolerancia": int(
        df_item_elegivel["DIF_BRUTO_DESC_LIQ"].abs().gt(TOLERANCIA_MONETARIA).sum()
    ),
    "diferenca_absoluta_total": df_item_elegivel["DIF_BRUTO_DESC_LIQ"].abs().sum(),
})

totais_item_nota = (
    df_item_elegivel.groupby(CHAVE_NOTA_INTERNA, as_index=False)
    .agg(
        ITEM_LIQUIDO=("VL_TOTALLIQUIDO", "sum"),
        ITEM_DESCONTO=("VL_TOTALDESC", "sum"),
        ITEM_QUANTIDADE=("QT_FATURADO", "sum"),
    )
)

reconciliacao_nota = df_nf_elegivel[
    CHAVE_NOTA_INTERNA + ["VL_TOTALPRODUTO", "VL_DESCONTO", "QT_FATURADO"]
].merge(totais_item_nota, on=CHAVE_NOTA_INTERNA, how="left", validate="one_to_one")

reconciliacao_nota["DIF_LIQUIDO"] = (
    reconciliacao_nota["ITEM_LIQUIDO"] - reconciliacao_nota["VL_TOTALPRODUTO"]
)
reconciliacao_nota["DIF_DESCONTO"] = (
    reconciliacao_nota["ITEM_DESCONTO"] - reconciliacao_nota["VL_DESCONTO"]
)
reconciliacao_nota["DIF_QUANTIDADE"] = (
    reconciliacao_nota["ITEM_QUANTIDADE"] - reconciliacao_nota["QT_FATURADO"]
)

resumo_reconciliacao = pd.DataFrame({
    "controle": ["Bruto - desconto = líquido", "Líquido item x cabeçalho", "Desconto item x cabeçalho", "Quantidade item x cabeçalho"],
    "registros_fora_tolerancia": [
        reconciliacao_item["linhas_fora_tolerancia"],
        int(reconciliacao_nota["DIF_LIQUIDO"].abs().gt(TOLERANCIA_MONETARIA).sum()),
        int(reconciliacao_nota["DIF_DESCONTO"].abs().gt(TOLERANCIA_MONETARIA).sum()),
        int(reconciliacao_nota["DIF_QUANTIDADE"].abs().gt(TOLERANCIA_MONETARIA).sum()),
    ],
})
display(resumo_reconciliacao)
"""),
        md("""
## 5. Visão consolidada

Todos os indicadores monetários usam os itens elegíveis. A quantidade aparece em quadro separado por unidade. O ticket usa o mesmo escopo do faturamento líquido e da contagem de documentos.
"""),
        code("""
faturamento_bruto = df_item_elegivel["VL_TOTALBRUTO"].sum()
valor_descontos = df_item_elegivel["VL_TOTALDESC"].sum()
faturamento_liquido = df_item_elegivel["VL_TOTALLIQUIDO"].sum()
quantidade_notas_distintas = df_nf_elegivel[CHAVE_DOCUMENTO_FISCAL].drop_duplicates().shape[0]
ticket_medio = (
    faturamento_liquido / quantidade_notas_distintas
    if quantidade_notas_distintas else np.nan
)

metricas_consolidadas = pd.DataFrame({
    "Métrica": [
        "Faturamento bruto", "Descontos", "Faturamento líquido comercial",
        "Notas fiscais distintas", "Ticket médio por nota",
    ],
    "Valor": [
        faturamento_bruto, valor_descontos, faturamento_liquido,
        quantidade_notas_distintas, ticket_medio,
    ],
    "Grão/Fonte": ["Item", "Item", "Item", "Cabeçalho", "Derivada"],
    "Regra": [
        "SUM(VL_TOTALBRUTO)", "SUM(VL_TOTALDESC)", "SUM(VL_TOTALLIQUIDO)",
        "DISTINCT DocumentoFiscalKey", "Líquido / notas distintas",
    ],
})

metricas_exibicao = metricas_consolidadas.copy()
metricas_exibicao["Valor"] = [
    f"R$ {faturamento_bruto:,.2f}",
    f"R$ {valor_descontos:,.2f}",
    f"R$ {faturamento_liquido:,.2f}",
    f"{quantidade_notas_distintas:,}",
    f"R$ {ticket_medio:,.2f}",
]
display(metricas_exibicao)
"""),
        code("""
quantidade_por_unidade = (
    df_item_elegivel.groupby("CD_ESPECIE", as_index=False, dropna=False)
    .agg(
        QUANTIDADE_FATURADA=("QT_FATURADO", "sum"),
        QUANTIDADE_ITENS=("NR_ITEM", "size"),
        FATURAMENTO_LIQUIDO=("VL_TOTALLIQUIDO", "sum"),
    )
    .sort_values("FATURAMENTO_LIQUIDO", ascending=False)
)
display(Markdown("### Quantidade faturada por unidade"))
display(quantidade_por_unidade)
"""),
        md("""
## 6. Evolução diária

Eixo temporal: `DT_FATURA`. Bruto, líquido, volume de documentos e ticket diário usam o mesmo escopo E/S.
"""),
        code("""
df_fat_diario = (
    df_item_elegivel.groupby("DT_FATURA", as_index=False)
    .agg(
        FATURAMENTO_BRUTO=("VL_TOTALBRUTO", "sum"),
        FATURAMENTO_LIQUIDO=("VL_TOTALLIQUIDO", "sum"),
    )
)

notas_diarias = (
    df_nf_elegivel.groupby("DT_FATURA", as_index=False)
    .agg(QUANTIDADE_NOTAS=("NR_FATURA", "nunique"))
)

df_fat_diario = df_fat_diario.merge(notas_diarias, on="DT_FATURA", validate="one_to_one")
df_fat_diario["TICKET_MEDIO"] = (
    df_fat_diario["FATURAMENTO_LIQUIDO"] / df_fat_diario["QUANTIDADE_NOTAS"]
)
df_fat_diario = df_fat_diario.sort_values("DT_FATURA")
display(df_fat_diario)
"""),
        code("""
fig, ax = plt.subplots(figsize=(13, 5))
ax.plot(df_fat_diario["DT_FATURA"], df_fat_diario["FATURAMENTO_BRUTO"], label="Bruto", linewidth=2)
ax.plot(df_fat_diario["DT_FATURA"], df_fat_diario["FATURAMENTO_LIQUIDO"], label="Líquido", linewidth=2)
ax.set(title="Evolução diária do faturamento", xlabel="DT_FATURA", ylabel="Valor")
ax.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
"""),
        md("""
## 7. Faturamento por empresa

Segmentação mantida para compatibilidade futura. Se houver uma única empresa, o relatório registra ausência de segmentação real.
"""),
        code("""
df_fat_empresa = (
    df_item_elegivel.groupby("CD_EMPRESA", as_index=False)
    .agg(
        FATURAMENTO_BRUTO=("VL_TOTALBRUTO", "sum"),
        FATURAMENTO_LIQUIDO=("VL_TOTALLIQUIDO", "sum"),
        DESCONTOS=("VL_TOTALDESC", "sum"),
    )
    .sort_values("FATURAMENTO_LIQUIDO", ascending=False)
)
display(df_fat_empresa)

if len(df_fat_empresa) == 1:
    display(Markdown("**Limitação:** o recorte possui uma única empresa; não existe comparação empresarial real."))

fig, ax = plt.subplots(figsize=(9, 4))
sns.barplot(data=df_fat_empresa, x="CD_EMPRESA", y="FATURAMENTO_LIQUIDO", ax=ax)
ax.set(title="Faturamento líquido por empresa", xlabel="Empresa", ylabel="Faturamento líquido")
plt.tight_layout()
plt.show()
"""),
        md("""
## 8. Principais produtos por faturamento

Ranking no grão do item, agrupado por `CD_PRODUTO`. Descrição representativa é mantida apenas como rótulo; produtos não são agrupados somente por descrição.
"""),
        code("""
produto_descricao = (
    df_item_elegivel.groupby(["CD_PRODUTO", "DS_PRODUTO"], dropna=False)
    .size().rename("FREQUENCIA").reset_index()
    .sort_values(["CD_PRODUTO", "FREQUENCIA"], ascending=[True, False])
    .drop_duplicates("CD_PRODUTO")
    [["CD_PRODUTO", "DS_PRODUTO"]]
)

df_produto_faturamento = (
    df_item_elegivel.groupby("CD_PRODUTO", as_index=False)
    .agg(
        FATURAMENTO_BRUTO=("VL_TOTALBRUTO", "sum"),
        DESCONTOS=("VL_TOTALDESC", "sum"),
        FATURAMENTO_LIQUIDO=("VL_TOTALLIQUIDO", "sum"),
    )
    .merge(produto_descricao, on="CD_PRODUTO", how="left", validate="one_to_one")
    .sort_values("FATURAMENTO_LIQUIDO", ascending=False)
)

top_produtos_faturamento = df_produto_faturamento.head(10).copy()
display(top_produtos_faturamento)

fig, ax = plt.subplots(figsize=(11, 6))
plot_fat = top_produtos_faturamento.sort_values("FATURAMENTO_LIQUIDO")
sns.barplot(data=plot_fat, x="FATURAMENTO_LIQUIDO", y="DS_PRODUTO", ax=ax)
ax.set(title="Top 10 produtos por faturamento líquido", xlabel="Faturamento líquido", ylabel="Produto")
plt.tight_layout()
plt.show()
"""),
        md("""
## 9. Principais produtos por quantidade

Quantidades são comparadas dentro de cada `CD_ESPECIE`. O quadro abaixo usa as unidades com maior faturamento líquido; nenhuma soma combina unidades incompatíveis.
"""),
        code("""
unidades_relevantes = quantidade_por_unidade.head(3)["CD_ESPECIE"].tolist()

df_produto_quantidade = (
    df_item_elegivel.groupby(["CD_ESPECIE", "CD_PRODUTO"], as_index=False, dropna=False)
    .agg(
        QUANTIDADE_FATURADA=("QT_FATURADO", "sum"),
        FATURAMENTO_LIQUIDO=("VL_TOTALLIQUIDO", "sum"),
    )
    .merge(produto_descricao, on="CD_PRODUTO", how="left", validate="many_to_one")
)

top_quantidade_por_unidade = (
    df_produto_quantidade[df_produto_quantidade["CD_ESPECIE"].isin(unidades_relevantes)]
    .sort_values(["CD_ESPECIE", "QUANTIDADE_FATURADA"], ascending=[True, False])
    .groupby("CD_ESPECIE", group_keys=False)
    .head(10)
)
display(top_quantidade_por_unidade)

for unidade in unidades_relevantes:
    dados = top_quantidade_por_unidade.loc[
        top_quantidade_por_unidade["CD_ESPECIE"].eq(unidade)
    ].sort_values("QUANTIDADE_FATURADA")
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=dados, x="QUANTIDADE_FATURADA", y="DS_PRODUTO", ax=ax)
    ax.set(title=f"Top produtos por quantidade — unidade {unidade}", xlabel="Quantidade", ylabel="Produto")
    plt.tight_layout()
    plt.show()
"""),
        md("""
## 10. Sensibilidade dos filtros fiscais

Esta seção não redefine o faturamento. Mostra impacto potencial de situação, operação, modelo fiscal e `CD_OPERACAO`, permitindo futura homologação.
"""),
        code("""
sensibilidade_situacao_operacao = (
    df_nf.groupby(["TP_SITUACAO", "TP_OPERACAO"], as_index=False, dropna=False)
    .agg(
        REGISTROS=("NR_FATURA", "size"),
        VL_TOTALPRODUTO=("VL_TOTALPRODUTO", "sum"),
        VL_TOTALNOTA=("VL_TOTALNOTA", "sum"),
    )
    .sort_values("VL_TOTALPRODUTO", ascending=False)
)

sensibilidade_modelo = (
    df_nf_elegivel.groupby("TP_MODDCTOFISCAL", as_index=False, dropna=False)
    .agg(
        REGISTROS=("NR_FATURA", "size"),
        VL_TOTALPRODUTO=("VL_TOTALPRODUTO", "sum"),
    )
    .sort_values("VL_TOTALPRODUTO", ascending=False)
)

sensibilidade_operacao = (
    df_nf_elegivel.groupby("CD_OPERACAO", as_index=False, dropna=False)
    .agg(
        REGISTROS=("NR_FATURA", "size"),
        VL_TOTALPRODUTO=("VL_TOTALPRODUTO", "sum"),
    )
    .sort_values("VL_TOTALPRODUTO", ascending=False)
)

display(Markdown("### Situação × tipo de operação"))
display(sensibilidade_situacao_operacao)
display(Markdown("### Modelos fiscais dentro do escopo E/S"))
display(sensibilidade_modelo)
display(Markdown("### CD_OPERACAO dentro do escopo E/S"))
display(sensibilidade_operacao)
"""),
        md("""
## 11. Regras aplicadas e limitações

### Regras aplicadas

1. Elegibilidade definida no cabeçalho por `TP_SITUACAO = 'E'` e `TP_OPERACAO = 'S'`.
2. Escopo propagado aos itens por `CD_EMPRESA + NR_FATURA`.
3. Métricas monetárias e produtos calculados nos itens.
4. Documento fiscal contado no cabeçalho pela chave composta definida.
5. Ticket calculado com líquido e documentos do mesmo escopo.
6. Quantidade comparada somente dentro da mesma `CD_ESPECIE`.
7. Valores do cabeçalho não são somados após o merge com itens.

### Limitações e validações pendentes

- Devoluções não possuem regra homologada; não foram abatidas por classificação de `CD_OPERACAO` ou CFOP.
- Cancelamentos e operações não comerciais são excluídos apenas conforme regra provisória E/S.
- `CD_OPERACAO` permanece sem classificação semântica.
- Modelo 55 é referência fiscal, mas outros modelos elegíveis permanecem no total até decisão formal.
- `DT_FATURA` foi adotada por premissa; eventual substituição por `DT_EMISSAO` mudará a análise temporal.
- Empresa pode não oferecer segmentação real no recorte atual.
- Resultados são analíticos e provisórios; publicação oficial depende de homologação fiscal e comercial.
"""),
        md("""
## 12. Conclusão operacional

O relatório entrega métricas mínimas e análises solicitadas dentro do escopo provisório aprovado. Próximo passo: homologar devoluções, CFOP, `CD_OPERACAO`, modelos fiscais e identidade oficial do documento antes da publicação gerencial definitiva.
"""),
    ]

    return new_notebook(
        cells=cells,
        metadata={
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3"},
        },
    )


def validate_notebook(notebook, require_outputs: bool = False) -> None:
    nbformat.validate(notebook)
    source = "\n".join(cell.source for cell in notebook.cells)
    required = [
        "Faturamento bruto", "Faturamento líquido", "Descontos",
        "Quantidade faturada", "Notas fiscais distintas", "Ticket médio",
        "Evolução diária", "Faturamento por empresa",
        "Principais produtos por faturamento", "Principais produtos por quantidade",
        "TP_SITUACAO", "TP_OPERACAO", "CD_ESPECIE", "CD_OPERACAO",
        "validate=\"many_to_one\"", "Valores do cabeçalho não são somados",
    ]
    missing = [term for term in required if term not in source]
    assert not missing, f"Conteúdo obrigatório ausente: {missing}"

    code_cells = [cell for cell in notebook.cells if cell.cell_type == "code"]
    errors = [
        output
        for cell in code_cells
        for output in cell.get("outputs", [])
        if output.get("output_type") == "error"
    ]
    assert not errors, f"Notebook contém {len(errors)} output(s) de erro"

    if require_outputs:
        assert all(cell.execution_count is not None for cell in code_cells)
        assert sum(bool(cell.get("outputs")) for cell in code_cells) >= 10


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--require-outputs", action="store_true")
    args = parser.parse_args()

    if args.validate_only:
        if not OUTPUT.exists():
            raise FileNotFoundError(OUTPUT)
        notebook = nbformat.read(OUTPUT, as_version=4)
        validate_notebook(notebook, require_outputs=args.require_outputs)
        print(f"Notebook válido: {OUTPUT}")
        return

    notebook = build_notebook()
    validate_notebook(notebook)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(notebook, OUTPUT)
    print(f"Notebook gerado: {OUTPUT}")


if __name__ == "__main__":
    main()
