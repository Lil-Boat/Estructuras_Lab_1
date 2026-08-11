"""TDA Cola de Prioridad implementado con nodos enlazados.

Reglas de orden:
  - Menor nivel de prioridad => se atiende primero (nivel 1 es el máximo).
  - Entre elementos del mismo nivel se respeta el orden de llegada (FIFO estable).
"""

from nodo import Nodo


class _ElementoPrioridad:
    """Empaqueta un comprador junto con su nivel de prioridad."""

    __slots__ = ("prioridad", "comprador")

    def __init__(self, prioridad, comprador):
        self.prioridad = prioridad
        self.comprador = comprador


class ColaPrioridad:
    """Cola de prioridad con nodos enlazados (sin arreglos ni listas)."""

    def __init__(self):
        self._frente = None
        self._tamano = 0

    def encolar(self, comprador, prioridad):
        """Inserta manteniendo el orden: mayor prioridad primero, FIFO entre iguales."""
        elemento = _ElementoPrioridad(prioridad, comprador)
        nodo = Nodo(elemento)

        # Caso: frente vacío o el nuevo tiene más prioridad que el frente.
        if self._frente is None or prioridad < self._frente.dato.prioridad:
            nodo.siguiente = self._frente
            self._frente = nodo
        else:
            # Avanza mientras el siguiente tenga prioridad MENOR O IGUAL,
            # así el nuevo queda después de los de su mismo nivel (FIFO).
            actual = self._frente
            while (actual.siguiente is not None
                   and actual.siguiente.dato.prioridad <= prioridad):
                actual = actual.siguiente
            nodo.siguiente = actual.siguiente
            actual.siguiente = nodo

        self._tamano += 1

    def desencolar(self):
        """Extrae y devuelve al comprador de mayor prioridad. Costo O(1)."""
        if self.esta_vacia():
            raise IndexError("No se puede desencolar de una cola de prioridad vacía.")
        nodo_frente = self._frente
        self._frente = self._frente.siguiente
        self._tamano -= 1
        return nodo_frente.dato.comprador

    def ver_frente(self):
        """Devuelve al siguiente comprador prioritario sin extraerlo (peek)."""
        if self.esta_vacia():
            return None
        return self._frente.dato.comprador

    def esta_vacia(self):
        """True si no hay elementos en la cola."""
        return self._frente is None

    def vaciar(self):
        """Elimina todos los elementos de la cola."""
        self._frente = None
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
            return "[Cola de prioridad vacía]"
        partes = []
        actual = self._frente
        while actual is not None:
            partes.append(f"(P{actual.dato.prioridad}) {actual.dato.comprador}")
            actual = actual.siguiente
        return " -> ".join(partes)