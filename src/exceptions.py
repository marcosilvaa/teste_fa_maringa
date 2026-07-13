"""Exceções diagnósticas do pipeline de dados."""


class DashboardDataError(RuntimeError):
    """Erro esperado e apresentável na carga ou validação dos dados."""


class DataSourceError(DashboardDataError):
    """Fonte ausente, ilegível ou incompatível."""


class SchemaValidationError(DashboardDataError):
    """Esquema ou conteúdo obrigatório inválido."""


class CardinalityError(DashboardDataError):
    """Chave ou cardinalidade incompatível com o modelo analítico."""
