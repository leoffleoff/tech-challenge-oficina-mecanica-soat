from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from app.domain.exceptions.domain_exceptions import BusinessRuleException


@dataclass
class Servico:
    nome: str
    descricao: str
    preco_base: Decimal
    tempo_estimado_minutos: int
    id: Optional[int] = None

    def __post_init__(self):
        if not self.nome or len(self.nome.strip()) < 3:
            raise BusinessRuleException("O nome do serviço deve ter pelo menos 3 caracteres.")
        self.preco_base = Decimal(str(self.preco_base))
        if self.preco_base <= Decimal("0.00"):
            raise BusinessRuleException("O preço base do serviço deve ser maior que zero.")
        if self.tempo_estimado_minutos <= 0:
            raise BusinessRuleException("O tempo estimado deve ser maior que zero minutos.")