"""Fábrica central de gráficos Plotly."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.config import COLORS
from src.formatting import format_brl, format_percentage, format_quantity


PLOT_CONFIG = {
    "displaylogo": False,
    "responsive": True,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
}


def _base_layout(fig: go.Figure, title: str, height: int = 440) -> go.Figure:
    fig.update_layout(
        title={"text": title, "x": 0.01, "xanchor": "left"},
        height=height,
        margin={"l": 18, "r": 18, "t": 64, "b": 26},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Avenir Next, Segoe UI, sans-serif", "color": COLORS["ink"]},
        hoverlabel={"bgcolor": "#FFFFFF", "font_size": 13},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0},
    )
    fig.update_xaxes(showgrid=False, linecolor=COLORS["grid"])
    fig.update_yaxes(gridcolor=COLORS["grid"], zerolinecolor=COLORS["grid"])
    return fig


def revenue_evolution(df: pd.DataFrame, moving_window: int | None = None) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["PERIODO"],
            y=df["faturamento_bruto"],
            name="Faturamento bruto",
            mode="lines+markers",
            line={"color": COLORS["gross"], "width": 2},
            customdata=[format_brl(value) for value in df["faturamento_bruto"]],
            hovertemplate="%{x|%d/%m/%Y}<br>Bruto: %{customdata}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["PERIODO"],
            y=df["faturamento_liquido"],
            name="Faturamento líquido",
            mode="lines+markers",
            line={"color": COLORS["net"], "width": 3},
            customdata=[format_brl(value) for value in df["faturamento_liquido"]],
            hovertemplate="%{x|%d/%m/%Y}<br>Líquido: %{customdata}<extra></extra>",
        )
    )
    if moving_window and moving_window > 1:
        moving = df["faturamento_liquido"].rolling(moving_window, min_periods=1).mean()
        fig.add_trace(
            go.Scatter(
                x=df["PERIODO"],
                y=moving,
                name=f"Média móvel ({moving_window})",
                mode="lines",
                line={"color": COLORS["discount"], "width": 2, "dash": "dot"},
                hovertemplate="%{x|%d/%m/%Y}<br>Média: R$ %{y:,.2f}<extra></extra>",
            )
        )
    fig.update_yaxes(title="Valor (R$)", tickprefix="R$ ", separatethousands=True)
    fig.update_xaxes(title="Período")
    return _base_layout(fig, "Evolução do faturamento bruto e líquido")


def returns_evolution(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure(
        go.Bar(
            x=df["PERIODO"],
            y=df["devolucoes"],
            marker_color=COLORS["returns"],
            customdata=[format_brl(value) for value in df["devolucoes"]],
            hovertemplate="%{x|%d/%m/%Y}<br>Devoluções: %{customdata}<extra></extra>",
        )
    )
    fig.update_yaxes(title="Valor devolvido (R$)", tickprefix="R$ ")
    return _base_layout(fig, "Devoluções por período", height=350)


def cumulative_revenue(df: pd.DataFrame) -> go.Figure:
    accumulated = df["faturamento_liquido"].cumsum()
    fig = go.Figure(
        go.Scatter(
            x=df["PERIODO"],
            y=accumulated,
            mode="lines",
            fill="tozeroy",
            line={"color": COLORS["net"], "width": 3},
            fillcolor="rgba(22,133,107,0.16)",
            customdata=[format_brl(value) for value in accumulated],
            hovertemplate="%{x|%d/%m/%Y}<br>Acumulado: %{customdata}<extra></extra>",
        )
    )
    fig.update_yaxes(title="Faturamento acumulado (R$)", tickprefix="R$ ")
    return _base_layout(fig, "Faturamento líquido acumulado", height=380)


def revenue_waterfall(kpis: dict[str, float]) -> go.Figure:
    fig = go.Figure(
        go.Waterfall(
            orientation="v",
            measure=["absolute", "relative", "relative", "total"],
            x=["Bruto", "Descontos", "Devoluções", "Líquido"],
            y=[
                kpis["faturamento_bruto"],
                -kpis["descontos"],
                -kpis["devolucoes"],
                kpis["faturamento_liquido"],
            ],
            text=[
                format_brl(kpis["faturamento_bruto"]),
                f"− {format_brl(kpis['descontos'])}",
                f"− {format_brl(kpis['devolucoes'])}",
                format_brl(kpis["faturamento_liquido"]),
            ],
            textposition="outside",
            connector={"line": {"color": COLORS["grid"]}},
            increasing={"marker": {"color": COLORS["gross"]}},
            decreasing={"marker": {"color": COLORS["returns"]}},
            totals={"marker": {"color": COLORS["net"]}},
            hovertemplate="%{x}<br>%{text}<extra></extra>",
        )
    )
    fig.update_yaxes(title="Valor (R$)", tickprefix="R$ ")
    return _base_layout(fig, "Do faturamento bruto ao líquido")


def company_revenue(df: pd.DataFrame, dimension: str = "CD_EMPFAT") -> go.Figure:
    plot = df.sort_values("faturamento_liquido")
    fig = go.Figure(
        go.Bar(
            x=plot["faturamento_liquido"],
            y=plot[dimension].astype(str),
            orientation="h",
            marker_color=COLORS["net"],
            customdata=np.column_stack(
                [
                    [format_brl(value) for value in plot["faturamento_liquido"]],
                    [format_percentage(value) for value in plot["participacao"]],
                ]
            ),
            hovertemplate="Empresa %{y}<br>Líquido: %{customdata[0]}<br>Participação: %{customdata[1]}<extra></extra>",
        )
    )
    fig.update_xaxes(title="Faturamento líquido (R$)", tickprefix="R$ ")
    return _base_layout(fig, "Faturamento líquido por empresa", height=360)


def operation_composition(df: pd.DataFrame, included_only: bool = False) -> go.Figure:
    plot = df.copy()
    if included_only:
        plot = plot.loc[plot["classificacao"].isin(["Venda incluída", "Devolução"])]
    plot = plot.sort_values("valor_liquido")
    colors = {
        "Venda incluída": COLORS["navy"],
        "Devolução": COLORS["returns"],
        "Operação excluída": COLORS["muted"],
    }
    fig = px.bar(
        plot,
        x="valor_liquido",
        y="CFOP_TIPO_OPERACAO",
        color="classificacao",
        orientation="h",
        color_discrete_map=colors,
        labels={
            "valor_liquido": "Valor líquido (R$)",
            "CFOP_TIPO_OPERACAO": "Tipo de operação",
            "classificacao": "Tratamento",
        },
    )
    fig.update_traces(hovertemplate="%{y}<br>Valor: R$ %{x:,.2f}<extra></extra>")
    return _base_layout(fig, "Composição por tipo de operação", height=500)


def top_products_revenue(df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    plot = df.nlargest(top_n, "faturamento_liquido").sort_values("faturamento_liquido")
    labels = (
        plot["CD_PRODUTO"].astype(str)
        + " · "
        + plot["DS_PRODUTO"].str.slice(0, 50)
        + " ["
        + plot["CD_ESPECIE"].astype(str)
        + "]"
    )
    fig = go.Figure(
        go.Bar(
            x=plot["faturamento_liquido"],
            y=labels,
            orientation="h",
            marker_color=COLORS["net"],
            customdata=np.column_stack(
                [
                    plot["CD_ESPECIE"],
                    [format_brl(value) for value in plot["devolucoes"]],
                    [format_brl(value) for value in plot["faturamento_liquido"]],
                ]
            ),
            hovertemplate=(
                "%{y}<br>Unidade: %{customdata[0]}<br>"
                "Faturamento líquido: %{customdata[2]}<br>"
                "Devoluções: %{customdata[1]}<extra></extra>"
            ),
        )
    )
    fig.update_xaxes(title="Faturamento líquido (R$)", tickprefix="R$ ")
    return _base_layout(fig, f"Top {top_n} produtos por faturamento líquido", height=520)


def top_products_quantity(df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    plot = df.nlargest(top_n, "quantidade_liquida").sort_values("quantidade_liquida")
    labels = (
        plot["CD_PRODUTO"].astype(str)
        + " · "
        + plot["DS_PRODUTO"].str.slice(0, 50)
        + " ["
        + plot["CD_ESPECIE"].astype(str)
        + "]"
    )
    fig = go.Figure()
    for column, label, color in [
        ("quantidade_faturada", "Faturada", COLORS["gross"]),
        ("quantidade_devolvida", "Devolvida", COLORS["returns"]),
        ("quantidade_liquida", "Líquida", COLORS["net"]),
    ]:
        fig.add_trace(
            go.Bar(
                x=plot[column],
                y=labels,
                name=label,
                orientation="h",
                marker_color=color,
                customdata=[format_quantity(value) for value in plot[column]],
                hovertemplate=f"%{{y}}<br>{label}: %{{customdata}}<extra></extra>",
            )
        )
    fig.update_layout(barmode="group")
    fig.update_xaxes(title="Quantidade")
    return _base_layout(fig, f"Top {top_n} produtos por quantidade líquida", height=560)


def product_scatter(df: pd.DataFrame, log_scale: bool = False) -> go.Figure:
    plot = df.loc[(df["quantidade_liquida"] > 0) & (df["faturamento_liquido"] > 0)].copy()
    fig = px.scatter(
        plot,
        x="quantidade_liquida",
        y="faturamento_liquido",
        color="CD_ESPECIE",
        size="devolucoes",
        size_max=28,
        hover_name="DS_PRODUTO",
        hover_data={
            "CD_PRODUTO": True,
            "CD_ESPECIE": True,
            "quantidade_liquida": ":.2f",
            "faturamento_liquido": ":.2f",
            "devolucoes": ":.2f",
        },
        log_x=log_scale,
        log_y=log_scale,
        labels={
            "quantidade_liquida": "Quantidade líquida",
            "faturamento_liquido": "Faturamento líquido (R$)",
            "CD_ESPECIE": "Unidade",
        },
    )
    return _base_layout(fig, "Quantidade líquida × faturamento líquido", height=520)


def revenue_by_unit(df: pd.DataFrame) -> go.Figure:
    plot = (
        df.groupby("CD_ESPECIE", as_index=False, dropna=False)
        .agg(faturamento_liquido=("faturamento_liquido", "sum"))
        .sort_values("faturamento_liquido", ascending=False)
    )
    fig = go.Figure(
        go.Bar(
            x=plot["CD_ESPECIE"],
            y=plot["faturamento_liquido"],
            marker_color=COLORS["navy"],
            customdata=[format_brl(value) for value in plot["faturamento_liquido"]],
            hovertemplate="Unidade %{x}<br>Faturamento líquido: %{customdata}<extra></extra>",
        )
    )
    fig.update_xaxes(title="Unidade / espécie")
    fig.update_yaxes(title="Faturamento líquido (R$)", tickprefix="R$ ")
    return _base_layout(fig, "Faturamento líquido por unidade", height=400)


def pareto_products(df: pd.DataFrame, top_n: int = 30, value: str = "faturamento_liquido") -> go.Figure:
    plot = df.sort_values(value, ascending=False).head(top_n).copy()
    total = float(df[value].sum())
    plot["acumulado"] = plot[value].cumsum() / total if total else 0.0
    labels = plot["CD_PRODUTO"].astype(str)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(x=labels, y=plot[value], name="Valor", marker_color=COLORS["navy"]),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=labels,
            y=plot["acumulado"],
            name="Participação acumulada",
            mode="lines+markers",
            line={"color": COLORS["discount"], "width": 3},
            customdata=[format_percentage(value) for value in plot["acumulado"]],
            hovertemplate="Produto %{x}<br>Acumulado: %{customdata}<extra></extra>",
        ),
        secondary_y=True,
    )
    value_label = "Devoluções" if value == "devolucoes" else "Faturamento líquido"
    fig.update_yaxes(title=f"{value_label} (R$)", tickprefix="R$ ", secondary_y=False)
    fig.update_yaxes(title="Participação acumulada", tickformat=".0%", range=[0, 1.05], secondary_y=True)
    fig.update_xaxes(title="Código do produto")
    return _base_layout(fig, f"Pareto de {value_label.lower()} — {top_n} produtos", height=460)


def return_ranking(
    df: pd.DataFrame,
    metric: str,
    title: str,
    top_n: int = 10,
    percentage: bool = False,
    quantity: bool = False,
) -> go.Figure:
    plot = df.nlargest(top_n, metric).sort_values(metric)
    labels = (
        plot["CD_PRODUTO"].astype(str)
        + " · "
        + plot["DS_PRODUTO"].str.slice(0, 48)
        + " ["
        + plot["CD_ESPECIE"].astype(str)
        + "]"
    )
    fig = go.Figure(
        go.Bar(
            x=plot[metric],
            y=labels,
            orientation="h",
            marker_color=COLORS["returns"],
            customdata=(
                [format_percentage(value) for value in plot[metric]]
                if percentage
                else (
                    [format_quantity(value) for value in plot[metric]]
                    if quantity
                    else [format_brl(value) for value in plot[metric]]
                )
            ),
            hovertemplate="%{y}<br>Valor: %{customdata}<extra></extra>",
        )
    )
    fig.update_xaxes(
        tickformat=".1%" if percentage else None,
        tickprefix=None if percentage or quantity else "R$ ",
    )
    return _base_layout(fig, title, height=500)


def sales_vs_returns(df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    plot = df.nlargest(top_n, "devolucoes").sort_values("devolucoes")
    labels = (
        plot["CD_PRODUTO"].astype(str)
        + " · "
        + plot["DS_PRODUTO"].str.slice(0, 46)
        + " ["
        + plot["CD_ESPECIE"].astype(str)
        + "]"
    )
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=plot["faturamento_apos_descontos"],
            y=labels,
            name="Faturamento após descontos",
            orientation="h",
            marker_color=COLORS["gross"],
        )
    )
    fig.add_trace(
        go.Bar(
            x=plot["devolucoes"],
            y=labels,
            name="Devoluções",
            orientation="h",
            marker_color=COLORS["returns"],
        )
    )
    fig.update_layout(barmode="group")
    fig.update_xaxes(title="Valor (R$)", tickprefix="R$ ")
    return _base_layout(fig, "Faturamento e devoluções por produto", height=540)


def excluded_operations(df: pd.DataFrame) -> go.Figure:
    plot = df.sort_values("valor_liquido")
    fig = go.Figure(
        go.Bar(
            x=plot["valor_liquido"],
            y=plot["CFOP_TIPO_OPERACAO"],
            orientation="h",
            marker_color=COLORS["muted"],
            customdata=[format_brl(value) for value in plot["valor_liquido"]],
            hovertemplate="%{y}<br>Valor movimentado: %{customdata}<extra></extra>",
        )
    )
    fig.update_xaxes(title="Valor movimentado fora da receita (R$)", tickprefix="R$ ")
    return _base_layout(fig, "Operações excluídas do faturamento", height=470)
