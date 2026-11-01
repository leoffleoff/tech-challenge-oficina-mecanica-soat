from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from app.domain.value_objects.cpf_cnpj import CpfCnpj
from app.domain.exceptions.domain_exceptions import BusinessRuleException


@dataclass
class Cliente:
    nome: str
    documento: CpfCnpj
    telefone: str
    email: str
    endereco: Optional[str] = None
    id: Optional[int] = None
    criado_em: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        if not self.nome or len(self.nome.strip()) < 3:
            raise BusinessRuleException("O nome do cliente deve ter pelo menos 3 caracteres.")
        if not self.email or "@" not in self.email:
            raise BusinessRuleException("O e-mail informado para o cliente é inválido.")
        if not self.telefone or len(self.telefone.strip()) < 8:
            raise BusinessRuleException("O telefone informado para o cliente é inválido.")
        if isinstance(self.documento, str):
            self.documento = CpfCnpj(self.documento)