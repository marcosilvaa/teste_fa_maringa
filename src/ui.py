"""Componentes compartilhados pelas páginas Streamlit."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from pathlib import Path

import streamlit as st

from src.charts import PLOT_CONFIG
from src.config import OFFICIAL_DATE, PROJECT_ROOT, get_config
from src.data_loader import load_source_data, source_signature
from src.exceptions import DashboardDataError
from src.filters import FilterSpec, filter_options
from src.models import AnalyticalBundle
from src.transformations import prepare_analytical_data


@st.cache_data(show_spinner="Validando e preparando dados fiscais...")
def _cached_pipeline(
    nf_path: str,
    item_path: str,
    signature: tuple[tuple[str, int, int], ...],
) -> AnalyticalBundle:
    nf, items = load_source_data(nf_path, item_path, signature)
    return prepare_analytical_data(nf, items)


def get_bundle() -> AnalyticalBundle:
    config = get_config()
    signature = source_signature(config.nf_path, config.item_path)
    return _cached_pipeline(
        str(config.nf_path.resolve()),
        str(config.item_path.resolve()),
        signature,
    )


def get_bundle_or_stop() -> AnalyticalBundle:
    try:
        return get_bundle()
    except DashboardDataError as exc:
        st.error("Não foi possível preparar os dados do dashboard.")
        st.code(str(exc), language=None)
        st.stop()


def setup_page(title: str, icon: str = "📊") -> None:
    st.set_page_config(
        page_title=f"{title} | F.A. Maringá",
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    css_path = PROJECT_ROOT / "assets" / "styles.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def page_header(kicker: str, title: str, description: str) -> None:
    st.markdown(
        f"""
        <section class="page-hero">
            <p class="eyebrow">{kicker}</p>
            <h1>{title}</h1>
            <p class="hero-copy">{description}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _reset_filters(prefix: str) -> None:
    for key in list(st.session_state):
        if key.startswith(prefix):
            del st.session_state[key]
    st.rerun()


def render_filters(
    bundle: AnalyticalBundle,
    prefix: str,
    include: Iterable[str] = (
        "date",
        "billing_company",
        "source_company",
        "product",
        "description",
        "unit",
        "tipi_group",
        "tipi_family",
        "item_type",
    ),
) -> FilterSpec:
    include_set = set(include)
    options = filter_options(bundle)
    st.sidebar.markdown("### Filtros")
    if st.sidebar.button("Limpar filtros", key=f"{prefix}_clear", width="stretch"):
        _reset_filters(prefix)

    dates = bundle.integrated[OFFICIAL_DATE].dropna()
    minimum = dates.min().date()
    maximum = dates.max().date()
    start_date = minimum
    end_date = maximum
    if "date" in include_set:
        date_range = st.sidebar.date_input(
            "Período de emissão",
            value=(minimum, maximum),
            min_value=minimum,
            max_value=maximum,
            format="DD/MM/YYYY",
            key=f"{prefix}_date",
        )
        if isinstance(date_range, Sequence) and len(date_range) == 2:
            start_date, end_date = date_range

    billing = ()
    if "billing_company" in include_set:
        billing = tuple(
            st.sidebar.multiselect(
                "Empresa de faturamento",
                options["billing_companies"],
                key=f"{prefix}_billing",
                placeholder="Todas",
            )
        )

    source = ()
    if "source_company" in include_set:
        source = tuple(
            st.sidebar.multiselect(
                "Empresa de origem",
                options["source_companies"],
                key=f"{prefix}_source",
                placeholder="Todas",
            )
        )

    operations = ()
    if "operation" in include_set:
        operations = tuple(
            st.sidebar.multiselect(
                "Tipo de operação",
                options["operations"],
                key=f"{prefix}_operation",
                placeholder="Todas",
            )
        )

    products = ()
    if "product" in include_set:
        products = tuple(
            st.sidebar.multiselect(
                "Código do produto",
                options["product_codes"],
                key=f"{prefix}_product",
                placeholder="Todos",
            )
        )

    query = ""
    if "description" in include_set:
        query = st.sidebar.text_input(
            "Buscar na descrição",
            key=f"{prefix}_description",
            placeholder="Ex.: colchão",
        )

    units = ()
    if "unit" in include_set:
        units = tuple(
            st.sidebar.multiselect(
                "Unidade / espécie",
                options["units"],
                key=f"{prefix}_unit",
                placeholder="Todas",
            )
        )

    tipi_groups = ()
    if "tipi_group" in include_set:
        tipi_groups = tuple(
            st.sidebar.multiselect(
                "TIPI Grupo Fiscal",
                options["tipi_groups"],
                key=f"{prefix}_tipi_group",
                placeholder="Todos",
            )
        )

    tipi_families = ()
    if "tipi_family" in include_set:
        tipi_families = tuple(
            st.sidebar.multiselect(
                "TIPI Família Comercial",
                options["tipi_families"],
                key=f"{prefix}_tipi_family",
                placeholder="Todas",
            )
        )

    item_types = ()
    if "item_type" in include_set:
        item_types = tuple(
            st.sidebar.multiselect(
                "Tipo Fiscal do Item",
                options["item_types"],
                key=f"{prefix}_item_type",
                placeholder="Todos",
            )
        )

    return FilterSpec(
        start_date=start_date,
        end_date=end_date,
        billing_companies=billing,
        source_companies=source,
        operations=operations,
        product_codes=products,
        description_query=query,
        units=units,
        tipi_groups=tipi_groups,
        tipi_families=tipi_families,
        item_types=item_types,
    )


def metric_grid(items: Sequence[tuple[str, str, str | None]], columns: int = 4) -> None:
    for start in range(0, len(items), columns):
        row = st.columns(columns)
        for container, item in zip(row, items[start : start + columns]):
            label, value, help_text = item
            container.metric(label, value, help=help_text)


def show_empty_state(message: str = "Nenhum registro atende aos filtros atuais.") -> None:
    st.info(message, icon="ℹ️")


def show_chart(fig) -> None:
    st.plotly_chart(fig, width="stretch", config=PLOT_CONFIG)


def section_title(title: str, description: str | None = None) -> None:
    st.markdown(f"<h2 class='section-title'>{title}</h2>", unsafe_allow_html=True)
    if description:
        st.caption(description)
