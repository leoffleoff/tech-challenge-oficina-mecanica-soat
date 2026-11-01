from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from app.domain.value_objects.placa import Placa
from app.domain.exceptions.domain_exceptions import BusinessRuleException


@dataclass
class Veiculo:
    placa: Placa
    marca: str
    modelo: str
    ano: int
    cliente_id: int
    cor: Optional[str] = None
    id: Optional[int] = None
    criado_em: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        if isinstance(self.placa, str):
            self.placa = Placa(self.placa)
        if not self.marca or not self.marca.strip():
            raise BusinessRuleException("A marca do veículo é obrigatória.")
        if not self.modelo or not self.modelo.strip():
            raise BusinessRuleException("O modelo do veículo é obrigatório.")
        ano_atual = datetime.now(timezone.utc).year
        if self.ano < 1900 or self.ano > (ano_atual + 1):
            raise BusinessRuleException(f"Ano do veículo inválido: {self.ano}.")