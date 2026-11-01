from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from app.domain.exceptions.domain_exceptions import (
    BusinessRuleException,
    InsufficientStockException,
)


@dataclass
class Peca:
    nome: str
    codigo_sku: str
    preco_unitario: Decimal
    quantidade_estoque: int
    estoque_minimo: int = 5
    id: Optional[int] = None

    def __post_init__(self):
        if not self.nome or len(self.nome.strip()) < 2:
            raise BusinessRuleException("O nome da peça/insumo é obrigatório.")
        if not self.codigo_sku or not self.codigo_sku.strip():
            raise BusinessRuleException("O código SKU da peça é obrigatório.")
        self.preco_unitario = Decimal(str(self.preco_unitario))
        if self.preco_unitario <= Decimal("0.00"):
            raise BusinessRuleException("O preço unitário da peça deve ser maior que zero.")
        if self.quantidade_estoque < 0:
            raise BusinessRuleException("A quantidade em estoque não pode ser negativa.")

    def baixar_estoque(self, quantidade: int) -> None:
        if quantidade <= 0:
            raise BusinessRuleException("A quantidade de baixa deve ser maior que zero.")
        if self.quantidade_estoque < quantidade:
            raise InsufficientStockException(
                f"Estoque insuficiente para a peça '{self.nome}'. "
                f"Disponível: {self.quantidade_estoque}, Solicitado: {quantidade}."
            )
        self.quantidade_estoque -= quantidade

    def repor_estoque(self, quantidade: int) -> None:
        if quantidade <= 0:
            raise BusinessRuleException("A quantidade de reposição deve ser maior que zero.")
        self.quantidade_estoque += quantidade

    @property
    def precisa_reposicao(self) -> bool:
        return self.quantidade_estoque <= self.estoque_minimo