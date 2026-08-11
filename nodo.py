"""TDA Nodo: unidad básica de memoria enlazada usada por las colas."""


class Nodo:
    """Nodo enlazado simple que almacena un dato y apunta al siguiente."""

    __slots__ = ("dato", "siguiente")

    def __init__(self, dato):
        self.dato = dato
        self.siguiente = None

    def __repr__(self):
        return f"Nodo({self.dato!r})"