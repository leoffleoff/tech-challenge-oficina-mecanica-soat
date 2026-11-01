import re
from dataclasses import dataclass
from app.domain.exceptions.domain_exceptions import InvalidDocumentException


@dataclass(frozen=True)
class CpfCnpj:
    """Value Object imutável para validação e formatação de CPF ou CNPJ."""
    value: str

    def __post_init__(self):
        cleaned = re.sub(r"\D", "", self.value or "")
        object.__setattr__(self, "value", cleaned)

        if len(cleaned) == 11:
            if not self._validate_cpf(cleaned):
                raise InvalidDocumentException(f"CPF inválido: {self.value}")
        elif len(cleaned) == 14:
            if not self._validate_cnpj(cleaned):
                raise InvalidDocumentException(f"CNPJ inválido: {self.value}")
        else:
            raise InvalidDocumentException(
                "Documento deve conter exatamente 11 dígitos (CPF) ou 14 dígitos (CNPJ)."
            )

    @property
    def document_type(self) -> str:
        return "CPF" if len(self.value) == 11 else "CNPJ"

    @property
    def formatted(self) -> str:
        v = self.value
        if len(v) == 11:
            return f"{v[:3]}.{v[3:6]}.{v[6:9]}-{v[9:]}"
        return f"{v[:2]}.{v[2:5]}.{v[5:8]}/{v[8:12]}-{v[12:]}"

    @staticmethod
    def _validate_cpf(cpf: str) -> bool:
        if cpf == cpf[0] * 11:
            return False

        for i in range(9, 11):
            total = sum(int(cpf[num]) * ((i + 1) - num) for num in range(0, i))
            digit = ((total * 10) % 11) % 10
            if digit != int(cpf[i]):
                return False
        return True

    @staticmethod
    def _validate_cnpj(cnpj: str) -> bool:
        if cnpj == cnpj[0] * 14:
            return False

        weights_first = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        weights_second = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

        total_1 = sum(int(cnpj[i]) * weights_first[i] for i in range(12))
        remainder_1 = total_1 % 11
        digit_1 = 0 if remainder_1 < 2 else 11 - remainder_1
        if int(cnpj[12]) != digit_1:
            return False

        total_2 = sum(int(cnpj[i]) * weights_second[i] for i in range(13))
        remainder_2 = total_2 % 11
        digit_2 = 0 if remainder_2 < 2 else 11 - remainder_2
        if int(cnpj[13]) != digit_2:
            return False

        return True

    def __str__(self) -> str:
        return self.value
    