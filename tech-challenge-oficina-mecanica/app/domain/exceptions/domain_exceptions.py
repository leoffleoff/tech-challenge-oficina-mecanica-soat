class DomainException(Exception):
    """Exceção base para erros de regras de negócio no domínio."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class InvalidDocumentException(DomainException):
    """Lançada quando o CPF ou CNPJ informado é inválido."""
    pass


class InvalidLicensePlateException(DomainException):
    """Lançada quando a placa do veículo não segue o padrão Mercosul ou antigo."""
    pass


class InvalidStatusTransitionException(DomainException):
    """Lançada quando ocorre uma tentativa inválida de mudança de status na OS."""
    pass


class InsufficientStockException(DomainException):
    """Lançada quando não há estoque suficiente de uma peça/insumo."""
    pass


class EntityNotFoundException(DomainException):
    """Lançada quando uma entidade não é encontrada no repositório."""
    pass


class BusinessRuleException(DomainException):
    """Lançada quando uma regra geral de negócio é violada."""
    pass