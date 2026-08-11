"""TDA Cola (FIFO) implementado con nodos enlazados.

El primero en entrar es el primero en salir. No usa listas ni arreglos.
"""

from nodo import Nodo


class Cola:
    """Cola estándar FIFO construida con nodos enlazados."""

    def __init__(self):
        self._frente = None
        self._final = None
        self._tamano = 0

    def encolar(self, dato):
        """Agrega un elemento al final de la cola. Costo O(1)."""
        nodo = Nodo(dato)
        if self._final is None:
            self._frente = nodo
        else:
            self._final.siguiente = nodo
        self._final = nodo
        self._tamano += 1

    def desencolar(self):
        """Extrae y devuelve el elemento del frente. Costo O(1)."""
        if self.esta_vacia():
            raise IndexError("No se puede desencolar de una cola vacía.")
        dato = self._frente.dato
        self._frente = self._frente.siguiente
        if self._frente is None:
            self._final = None
        self._tamano -= 1
        return dato

    def ver_frente(self):
        """Devuelve el elemento del frente sin extraerlo (peek)."""
        if self.esta_vacia():
            return None
        return self._frente.dato

    def esta_vacia(self):
        """True si no hay elementos en la cola."""
        return self._frente is None

    def vaciar(self):
        """Elimina todos los elementos de la cola."""
        self._frente = None
        self._final = None
        self._tamano = 0

    @property
    def tamano(self):
        return self._tamano

    def __len__(self):
        return self._tamano

    def __bool__(self):
        return not self.esta_vacia()

    def __str__(self):
        if self.esta_vacia():
            return "[Cola vacía]"
        partes = []
        actual = self._frente
        while actual is not None:
            partes.append(str(actual.dato))
            actual = actual.siguiente
        return " -> ".join(partes)