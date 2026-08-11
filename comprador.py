"""Modelo de datos del comprador que entra a la fila virtual."""

from dataclasses import dataclass


@dataclass
class Comprador:
    """Representa a una persona esperando comprar una entrada.

    Categorías:
      - Regular: fila normal (FIFO).
      - VIP: membresía anual -> cola de prioridad (nivel 2).
      - Preferencial (Ley 7600): adulto mayor, embarazada o discapacidad
        -> cola de prioridad (nivel 1 = máxima).
    """

    REGULAR = "Regular"
    VIP = "VIP"
    PREFERENCIAL = "Preferencial (Ley 7600)"

    # Número menor = prioridad mayor. Regular no tiene prioridad (None).
    _PRIORIDAD_POR_CATEGORIA = {
        PREFERENCIAL: 1,
        VIP: 2,
        REGULAR: None,
    }

    nombre: str
    cedula: str
    categoria: str

    @property
    def prioridad(self):
        """Nivel de prioridad del comprador (None si es Regular)."""
        return self._PRIORIDAD_POR_CATEGORIA.get(self.categoria)

    @property
    def es_prioritario(self):
        """True si debe ir a la cola de prioridad (VIP o Preferencial)."""
        return self.prioridad is not None

    def __str__(self):
        return f"{self.nombre} (Céd. {self.cedula}) | {self.categoria}"