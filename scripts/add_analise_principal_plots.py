from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell


NOTEBOOK = Path(__file__).resolve().parents[1] / "notebooks" / "analise_principal.ipynb"
TAG_PREFIX = "analise-visual-"


def visual_cell(tag, source):
    cell = new_code_cell(source.strip())
    cell.metadata["tags"] = [f"{TAG_PREFIX}{tag}"]
    return cell


def insert_after(cells, marker, new_cells):
    for index, cell in enumerate(cells):
        if marker in cell.source:
            cells[index + 1:index + 1] = new_cells
            return
    raise ValueError(f"Marcador não encontrado: {marker}")


notebook = nbformat.read(NOTEBOOK, as_version=4)

for cell in notebook.cells:
    if cell.cell_type == "code" and "import seaborn as sns" in cell.source:
        if "%matplotlib inline" not in cell.source:
            cell.source = "%matplotlib inline\n" + cell.source
        break

# Execução idempotente: remove somente visuais criados por este script.
notebook.cells = [
    cell
    for cell in notebook.cells
    if not any(tag.startswith(TAG_PREFIX) for tag in cell.metadata.get("tags", []))
]

# Remove gráfico genérico anterior; será substituído por visual mais legível.
notebook.cells = [
    cell
    for cell in notebook.cells
    if cell.source.strip() != "evolucao_diaria.plot(figsize=(16,5))"
]

insert_after(
    notebook.cells,
    "distribuicao_operacoes",
    [visual_cell("operacoes", r'''
# Valor líquido por natureza fiscal: vendas, devoluções e operações excluídas.
operacoes_plot = distribuicao_operacoes.copy()
operacoes_plot["classificacao"] = np.select(
    [
        operacoes_plot["CFOP_TIPO_OPERACAO"].isin([
            "VENDA", "VENDA NAO CONTRIBUINTE", "VENDA SEM TRANSITO"
        ]),
        operacoes_plot["CFOP_TIPO_OPERACAO"].eq("DEVOLUCAO"),
    ],
    ["Venda incluída", "Devolução"],
    default="Operação excluída",
)
operacoes_plot = operacoes_plot.sort_values("valor_liquido")

fig, ax = plt.subplots(figsize=(12, 8))
sns.barplot(
    data=operacoes_plot,
    x="valor_liquido",
    y="CFOP_TIPO_OPERACAO",
    hue="classificacao",
    dodge=False,
    palette={
        "Venda incluída": "#2E86AB",
        "Devolução": "#D1495B",
        "Operação excluída": "#A8A8A8",
    },
    ax=ax,
)
ax.set(
    title="Valor líquido por tipo de operação fiscal",
    xlabel="Valor líquido (R$)",
    ylabel="Tipo de operação",
)
ax.legend(title="Tratamento analítico", loc="lower right")
ax.ticklabel_format(style="plain", axis="x")
plt.tight_layout()
plt.show()
''')],
)

insert_after(
    notebook.cells,
    "df_item_venda.groupby(",
    [visual_cell("mix-vendas", r'''
# Composição do faturamento entre as três operações de venda elegíveis.
mix_vendas = (
    df_item_venda.groupby("CFOP_TIPO_OPERACAO", as_index=False)
    .agg(faturamento_liquido=("VL_TOTALLIQUIDO", "sum"))
    .sort_values("faturamento_liquido", ascending=False)
)
mix_vendas["participacao"] = (
    mix_vendas["faturamento_liquido"] / mix_vendas["faturamento_liquido"].sum()
)

fig, ax = plt.subplots(figsize=(10, 5))
sns.barplot(
    data=mix_vendas,
    x="faturamento_liquido",
    y="CFOP_TIPO_OPERACAO",
    color="#2E86AB",
    ax=ax,
)
for container in ax.containers:
    ax.bar_label(
        container,
        labels=[f"{p:.1%}" for p in mix_vendas["participacao"]],
        padding=4,
    )
ax.set(
    title="Composição do faturamento líquido por operação de venda",
    xlabel="Faturamento líquido (R$)",
    ylabel="Operação",
)
plt.tight_layout()
plt.show()
''')],
)

insert_after(
    notebook.cells,
    "faturamento_liquido = (faturamento_liquido_vendas - valor_devolucoes)",
    [
        visual_cell("ponte", r'''
# Ponte entre faturamento bruto e líquido.
valor_descontos_plot = df_item_venda["VL_TOTALDESC"].sum()
apos_descontos = faturamento_bruto - valor_descontos_plot
etapas = ["Bruto", "Descontos", "Devoluções", "Líquido"]
valores = [faturamento_bruto, -valor_descontos_plot, -valor_devolucoes, faturamento_liquido]
bases = [0, apos_descontos, faturamento_liquido, 0]
alturas = [faturamento_bruto, valor_descontos_plot, valor_devolucoes, faturamento_liquido]
cores = ["#2E86AB", "#F4A261", "#D1495B", "#2A9D8F"]

fig, ax = plt.subplots(figsize=(11, 6))
ax.bar(etapas, alturas, bottom=bases, color=cores, width=0.65)
for i, (valor, base, altura) in enumerate(zip(valores, bases, alturas)):
    sinal = "" if i in (0, 3) else "− "
    ax.text(i, base + altura + faturamento_bruto * 0.018, f"{sinal}{format_brl(abs(valor))}", ha="center", fontweight="bold")
ax.set(title="Ponte do faturamento bruto ao líquido", ylabel="Valor (R$)")
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()
plt.show()
'''),
    ],
)

insert_after(
    notebook.cells,
    "ticket_medio = (",
    [visual_cell("kpis", r'''
# Painel consolidado dos principais indicadores.
kpis = [
    ("Faturamento bruto", format_brl(faturamento_bruto)),
    ("Descontos", format_brl(valor_descontos)),
    ("Devoluções", format_brl(valor_devolucoes)),
    ("Faturamento líquido", format_brl(faturamento_liquido)),
    ("Notas distintas", format_qtd(quantidade_notas)),
    ("Ticket médio", format_brl(ticket_medio)),
]

fig, axes = plt.subplots(2, 3, figsize=(15, 6))
for ax, (titulo, valor) in zip(axes.flat, kpis):
    ax.axis("off")
    ax.text(0.5, 0.62, valor, ha="center", va="center", fontsize=19, fontweight="bold", color="#16324F")
    ax.text(0.5, 0.32, titulo, ha="center", va="center", fontsize=11, color="#4F5D75")
    ax.add_patch(plt.Rectangle((0.03, 0.08), 0.94, 0.82, fill=False, linewidth=1.5, edgecolor="#D9E2EC"))
fig.suptitle("Visão consolidada do faturamento", fontsize=16, fontweight="bold")
plt.tight_layout()
plt.show()
''')],
)

insert_after(
    notebook.cells,
    "quantidade_liquida = (",
    [visual_cell("volume-tipo-item", r'''
# Composição da quantidade vendida por tipo fiscal do item.
volume_tipo_item = (
    df_item_venda.groupby("TIPO_ITEM_FISCAL", as_index=False, dropna=False)
    .agg(quantidade_faturada=("QT_FATURADO", "sum"))
    .sort_values("quantidade_faturada", ascending=False)
)

fig, ax = plt.subplots(figsize=(10, 5))
sns.barplot(
    data=volume_tipo_item,
    x="quantidade_faturada",
    y="TIPO_ITEM_FISCAL",
    color="#457B9D",
    ax=ax,
)
ax.set(
    title="Quantidade vendida por tipo fiscal do item",
    xlabel="Quantidade faturada",
    ylabel="Tipo fiscal",
)
for container in ax.containers:
    ax.bar_label(container, fmt="%.0f", padding=3)
plt.tight_layout()
plt.show()
''')],
)

insert_after(
    notebook.cells,
    'format_brl(evolucao_diaria["faturamento_liquido"].sum())',
    [visual_cell("evolucao-diaria", r'''
# Evolução diária: linhas para faturamento e barras para devoluções.
fig, (ax1, ax2) = plt.subplots(
    2, 1, figsize=(15, 8), sharex=True,
    gridspec_kw={"height_ratios": [2.2, 1]},
)
sns.lineplot(
    data=evolucao_diaria,
    x="DT_EMISSAO",
    y="faturamento_bruto",
    label="Bruto",
    color="#2E86AB",
    linewidth=2.2,
    ax=ax1,
)
sns.lineplot(
    data=evolucao_diaria,
    x="DT_EMISSAO",
    y="faturamento_liquido",
    label="Líquido",
    color="#2A9D8F",
    linewidth=2.2,
    ax=ax1,
)
ax1.set(title="Evolução diária do faturamento", xlabel="", ylabel="Valor (R$)")
ax1.legend()

ax2.bar(
    evolucao_diaria["DT_EMISSAO"],
    evolucao_diaria["devolucoes"],
    color="#D1495B",
    alpha=0.8,
)
ax2.set(title="Devoluções por dia", xlabel="Data de emissão", ylabel="Devoluções (R$)")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
''')],
)

insert_after(
    notebook.cells,
    "top_10_produtos_faturamento = (",
    [
        visual_cell("top-faturamento", r'''
# Top 10 produtos: faturamento líquido e valor devolvido.
plot_produtos_fat = top_10_produtos_faturamento.copy()
plot_produtos_fat["rotulo"] = plot_produtos_fat["DS_PRODUTO"].str.slice(0, 48)
plot_produtos_fat = plot_produtos_fat.sort_values("faturamento_liquido")

fig, ax = plt.subplots(figsize=(12, 7))
sns.barplot(
    data=plot_produtos_fat,
    x="faturamento_liquido",
    y="rotulo",
    color="#2A9D8F",
    ax=ax,
)
ax.scatter(
    plot_produtos_fat["devolucoes"],
    plot_produtos_fat["rotulo"],
    color="#D1495B",
    s=55,
    label="Devoluções",
    zorder=3,
)
ax.set(
    title="Top 10 produtos por faturamento líquido",
    xlabel="Valor (R$)",
    ylabel="Produto",
)
ax.legend()
plt.tight_layout()
plt.show()
'''),
        visual_cell("taxa-devolucao", r'''
# Taxa de devolução dos produtos líderes em faturamento.
taxa_devolucao_produto = top_10_produtos_faturamento.copy()
taxa_devolucao_produto["taxa_devolucao"] = np.where(
    taxa_devolucao_produto["faturamento_apos_descontos"].ne(0),
    taxa_devolucao_produto["devolucoes"] / taxa_devolucao_produto["faturamento_apos_descontos"] * 100,
    0,
)
taxa_devolucao_produto["rotulo"] = taxa_devolucao_produto["DS_PRODUTO"].str.slice(0, 48)
taxa_devolucao_produto = taxa_devolucao_produto.sort_values("taxa_devolucao")

fig, ax = plt.subplots(figsize=(12, 7))
sns.barplot(
    data=taxa_devolucao_produto,
    x="taxa_devolucao",
    y="rotulo",
    color="#E76F51",
    ax=ax,
)
ax.set(
    title="Taxa de devolução — Top 10 produtos por faturamento",
    xlabel="Devoluções / vendas líquidas antes da devolução (%)",
    ylabel="Produto",
)
for container in ax.containers:
    ax.bar_label(container, fmt="%.1f%%", padding=3)
plt.tight_layout()
plt.show()
'''),
    ],
)

insert_after(
    notebook.cells,
    "top_10_produtos_quantidade = quantidade_por_produto.head(10)",
    [visual_cell("top-quantidade", r'''
# Top 10 produtos: quantidade faturada, devolvida e líquida.
plot_produtos_qtd = top_10_produtos_quantidade.copy()
plot_produtos_qtd["rotulo"] = plot_produtos_qtd["DS_PRODUTO"].str.slice(0, 48)
plot_produtos_qtd = plot_produtos_qtd.melt(
    id_vars=["rotulo"],
    value_vars=["quantidade_faturada", "quantidade_devolvida", "quantidade_liquida"],
    var_name="metrica",
    value_name="quantidade",
)
plot_produtos_qtd["metrica"] = plot_produtos_qtd["metrica"].map({
    "quantidade_faturada": "Faturada",
    "quantidade_devolvida": "Devolvida",
    "quantidade_liquida": "Líquida",
})

fig, ax = plt.subplots(figsize=(12, 8))
sns.barplot(
    data=plot_produtos_qtd,
    x="quantidade",
    y="rotulo",
    hue="metrica",
    palette={"Faturada": "#2E86AB", "Devolvida": "#D1495B", "Líquida": "#2A9D8F"},
    ax=ax,
)
ax.set(
    title="Top 10 produtos por quantidade líquida",
    xlabel="Quantidade (unidade UN)",
    ylabel="Produto",
)
ax.legend(title="Métrica")
plt.tight_layout()
plt.show()
''')],
)

nbformat.validate(notebook)
nbformat.write(notebook, NOTEBOOK)
print(f"Visualizações inseridas em {NOTEBOOK}")
