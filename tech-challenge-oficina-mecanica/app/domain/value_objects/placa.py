import re
from dataclasses import dataclass
from app.domain.exceptions.domain_exceptions import InvalidLicensePlateException


@dataclass(frozen=True)
class Placa:
    """Value Object imutável para validação de Placa de Veículo (Antiga e Mercosul)."""
    value: str

    # Padrão Antigo (ABC1234) ou Padrão Mercosul (ABC1D23)
    PLATE_REGEX = re.compile(r"^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$")

    def __post_init__(self):
        if not self.value:
            raise InvalidLicensePlateException("A placa do veículo não pode ser vazia.")

        cleaned = re.sub(r"[^A-Za-z0-9]", "", self.value).upper()
        object.__setattr__(self, "value", cleaned)

        if not self.PLATE_REGEX.match(cleaned):
            raise InvalidLicensePlateException(
                f"Placa '{self.value}' inválida. Use o formato ABC1234 ou Mercosul ABC1D23."
            )

    @property
    def is_mercosul(self) -> bool:
        return self.value[4].isalpha()

    @property
    def formatted(self) -> str:
        if self.is_mercosul:
            return self.value
        return f"{self.value[:3]}-{self.value[3:]}"

    def __str__(self) -> str:
        return self.value