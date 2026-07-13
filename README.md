# Dashboard de Faturamento — F.A. Maringá

Aplicação Streamlit multipágina para análise executiva e auditável de faturamento, descontos, devoluções, produtos, empresas, operações e qualidade dos dados fiscais.

## Estrutura do projeto

```text
app.py                         Entrada da aplicação
pages/                         Cinco páginas analíticas
src/config.py                  Contratos, caminhos e regras estáveis
src/data_loader.py             Leitura tipada e cache por assinatura
src/data_validation.py         Esquema, datas, chaves e cardinalidade
src/transformations.py         Elegibilidade, merge e classificação
src/filters.py                 Filtros compartilhados
src/metrics.py                 KPIs e agregações reutilizáveis
src/charts.py                  Gráficos Plotly
src/formatting.py              Formatação de valores, percentuais e datas em pt-BR
src/ui.py                      Componentes Streamlit compartilhados
assets/styles.css              Identidade visual responsiva
tests/                         Testes de dados, métricas, filtros e páginas
data/                          CSVs originais e tratados
notebooks/                     Análises exploratórias e análise principal
```

## Páginas do Streamlit

- **Visão Geral:** KPIs, destaques, evolução temporal, composição do faturamento, produtos líderes e tabela diária.
- **Produtos:** indicadores do portfólio, rankings por faturamento e quantidade, relação entre volume e valor e tabela analítica.
- **Devoluções:** indicadores de retorno, evolução diária, rankings de produtos, taxas materiais e tabela de risco.
- **Empresas e Operações:** visão empresarial, operações fiscais e movimentos excluídos do faturamento.
- **Metodologia e Qualidade:** regras analíticas, cobertura dos dados, nulidade, consistência e auditoria.

## Fontes de dados

- `data/NF.csv`: cabeçalhos tratados das notas fiscais.
- `data/NFITEM.csv`: itens tratados e classificados.
- `data/FIS_NF.csv` e `data/FIS_NFITEM.csv`: fontes originais preservadas.

Os CSVs tratados são a origem oficial do dashboard. Nenhum arquivo-fonte é alterado pela aplicação.

Os caminhos podem ser configurados sem alterar código:

```bash
export FAMARINGA_DATA_DIR=/caminho/para/dados
export FAMARINGA_NF_PATH=/caminho/NF.csv
export FAMARINGA_NFITEM_PATH=/caminho/NFITEM.csv
```

## Regras de negócio

- Nota válida: `TP_SITUACAO = 'E'`.
- Chave do merge: `CD_EMPRESA + CD_EMPFAT + NR_FATURA + DT_FATURA`.
- Cardinalidade: muitos itens para um cabeçalho (`many_to_one`).
- Data oficial: `DT_EMISSAO`.
- Vendas: `VENDA`, `VENDA CONSUMIDOR FINAL` e `VENDA SEM TRANSITO`.
- Devolução: `DEVOLUCAO`, fluxo `ENTRADA`, item `PRODUTO`.
- Nota distinta: `CD_EMPFAT + CD_SERIE + NR_NF`, somente documentos com venda.
- Faturamento bruto: soma de `VL_TOTALBRUTO` das vendas.
- Descontos: soma de `VL_TOTALDESC` das vendas; descontos das devoluções não entram.
- Faturamento após descontos: soma de `VL_TOTALLIQUIDO` das vendas.
- Faturamento líquido: faturamento após descontos menos devoluções líquidas.
- Ticket médio: faturamento do recorte dividido pelas notas distintas do mesmo recorte.
- Quantidades por produto preservam `CD_ESPECIE`.

Transferências, aquisições de transporte e ISSQN, depósitos, retornos, bonificações, uso/consumo, ativo imobilizado, outras operações e ajustes não entram na receita. Permanecem disponíveis para auditoria.

`Faturamento líquido` significa faturamento líquido comercial após descontos e devoluções. Não representa receita líquida contábil após tributos.

## Filtros

As páginas analíticas aplicam os mesmos filtros sobre vendas, devoluções e operações excluídas:

- período de emissão;
- empresa de faturamento;
- empresa de origem;
- produto e descrição;
- unidade ou espécie;
- tipo de operação, quando aplicável;
- `TIPI Grupo Fiscal`;
- `TIPI Família Comercial`;
- `Tipo Fiscal do Item`.

## Instalação

Requisito: Python 3.13 ou superior.

### Via Poetry

```bash
poetry install
```

### Via pip

Crie e ative um ambiente virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Instale as dependências:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Execução

Pela raiz do repositório:

```bash
poetry run streamlit run app.py
```

Com o ambiente virtual ativado, também funciona:

```bash
streamlit run app.py
```

## Testes

```bash
poetry run python -m pytest -q
```

O uso de `python -m pytest` garante que a raiz do projeto participe do caminho de importação.

## Atualização dos dados e cache

Substitua `NF.csv` e `NFITEM.csv` pelos novos arquivos tratados, preservando o esquema obrigatório. O cache usa uma assinatura composta por:

- caminho resolvido;
- tamanho do arquivo;
- horário de modificação em nanossegundos.

Qualquer alteração em uma fonte muda a assinatura e invalida automaticamente leitura e processamento no `st.cache_data`.

## Camada Parquet

Não foi criada nesta versão. Os CSVs tratados somam aproximadamente 25 MB e o cache em memória atende o volume atual. Caso o histórico cresça, uma camada Parquet poderá ser adicionada, mantendo os CSVs como origem oficial e usando a mesma assinatura para invalidação.

## Notebooks de referência

- `notebooks/01_analise_nf.ipynb`: exploração e tratamento dos cabeçalhos.
- `notebooks/02_analise_nfitem.ipynb`: exploração, CFOP, TIPI e classificação dos itens.
- `notebooks/03_analise_faturamento.ipynb`: fonte principal das regras e métricas reproduzidas.

Os notebooks documentam a exploração, classificação fiscal e validação das métricas.
O Streamlit reproduz essas regras em módulos reutilizáveis dentro de `src/`, evitando
fórmulas diferentes entre a análise e o dashboard.

## Limitações conhecidas

- O conjunto atual possui somente `CD_EMPFAT = 6`; não permite comparação real entre empresas faturadoras.
- Devoluções são registradas na data de emissão da nota de devolução.
- Não existe vínculo explícito da devolução com a operação ou data da venda original; portanto, não há retroação temporal.
- A análise cobre o período fiscal fechado de março de 2026 em `DT_EMISSAO`.
- Causas de devolução, margem, custos, impostos e clientes não foram fornecidos ou não integram o escopo atual.
