import re

from rest_framework import serializers

# Formato colombiano estándar: 3 letras + 3 dígitos (ej: ABC123)
_PLATE_RE = re.compile(r"^[A-Z]{3}\d{3}$")


def validate_plate_format(value: str) -> str:
    value = value.upper().strip()
    if not _PLATE_RE.match(value):
        raise serializers.ValidationError(
            "Formato de placa inválido. Debe ser 3 letras seguidas de 3 dígitos (ej: ABC123)."
        )
    return value
