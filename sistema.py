"""Motor de filas del sistema Ticket UNA.

Contiene la lógica de despacho (3 prioritarios por cada 1 regular),
el control de las 500 entradas y la regla de SOLD OUT.
"""

import random
from collections import Counter

from cola import Cola
from cola_prioridad import ColaPrioridad
from comprador import Comprador

# ---------------------------------------------------------------------------
# Datos para la simulación masiva (bonus)
# ---------------------------------------------------------------------------
_NOMBRES = [
    "Ana", "Carlos", "María", "José", "Sofía", "Diego", "Valeria", "Andrés",
    "Camila", "Luis", "Gabriela", "Jorge", "Daniela", "Fabián", "Lucía",
    "Kevin", "Natalia", "Esteban", "Paula", "Marco", "Raquel", "Oscar",
    "Karla", "Manuel", "Rosa", "Freddy", "Adriana", "Pablo", "Melissa",
    "Roberto",
]

_APELLIDOS = [
    "Rodríguez", "Vargas", "Mora", "Jiménez", "Soto", "Rojas", "Cruz",
    "Aguilar", "Chaves", "Ramírez", "Herrera", "Castro", "Gutiérrez",
    "Méndez", "Solano", "Alfaro", "Zúñiga", "Quesada", "Picado", "Salazar",
    "Fernández", "Ureña", "Sanabria", "Campos", "Bonilla", "Garita",
    "Álvarez",
]


def _generar_comprador_aleatorio():
    """Crea un comprador con datos aleatorios ticos (para la simulación)."""
    nombre = f"{random.choice(_NOMBRES)} {random.choice(_APELLIDOS)}"
    cedula = f"{random.randint(1, 9)}{random.randint(0, 99_999_999):08d}"
    categoria = random.choices(
        (Comprador.REGULAR, Comprador.VIP, Comprador.PREFERENCIAL),
        weights=(50, 30, 20),
    )[0]
    return Comprador(nombre, cedula, categoria)


class SistemaBoletaje:
    """Sistema de boletaje: fila regular (FIFO) + fila de prioridad."""

    TOTAL_ENTRADAS_DEFECTO = 500
    RATIO_PRIORITARIOS_POR_REGULAR = 3

    def __init__(self, total_entradas=TOTAL_ENTRADAS_DEFECTO):
        self.cola_regular = Cola()
        self.cola_prioridad = ColaPrioridad()
        self.total_entradas = total_entradas
        self.entradas_restantes = total_entradas
        self.vendidas_por_categoria = Counter()
        self.sold_out = False
        self.vendedor_registrado = None
        # Contador interno de la regla 3:1.
        self._prioritarios_consecutivos = 0

    # ------------------------------------------------------------------
    # Cuentas del vendedor (registro y acceso)
    # ------------------------------------------------------------------
    def registrar_vendedor(self, nombre, contrasena):
        """Guarda las credenciales de un vendedor en el sistema."""
        self.vendedor_registrado = {"nombre": nombre, "contrasena": contrasena}
        return self.vendedor_registrado

    def iniciar_sesion_vendedor(self, nombre, contrasena):
        """Valida las credenciales guardadas. Devuelve el vendedor o None."""
        vendedor = self.vendedor_registrado
        if (vendedor is not None
                and vendedor["nombre"] == nombre
                and vendedor["contrasena"] == contrasena):
            return vendedor
        return None

    # ------------------------------------------------------------------
    # Registro de compradores
    # ------------------------------------------------------------------
    def registrar_comprador(self, comprador):
        """Encola a un comprador en la fila que le corresponde por categoría."""
        if self.sold_out:
            raise ValueError("SOLD OUT: las entradas están agotadas, venta cerrada.")
        if comprador.es_prioritario:
            self.cola_prioridad.encolar(comprador, comprador.prioridad)
        else:
            self.cola_regular.encolar(comprador)

    # ------------------------------------------------------------------
    # Despacho (requerimiento #2)
    # ------------------------------------------------------------------
    def atender_siguiente(self):
        """Extrae al siguiente comprador (regla 3:1) y descuenta una entrada.

        Secuencia de despacho: P P P R P P P R ...
        Si la cola de prioridad está vacía, se atiende solo a la regular.
        Al llegar a 0 entradas se emite SOLD OUT y se vacían las colas.
        """
        if self.sold_out:
            return self._resultado("sold_out")

        comprador = self._siguiente_por_algoritmo()
        if comprador is None:
            return self._resultado("sin_clientes")

        self.entradas_restantes -= 1
        self.vendidas_por_categoria[comprador.categoria] += 1

        if self.entradas_restantes == 0:
            self.sold_out = True
            self._vaciar_colas()
            return self._resultado("ultima_entrada", comprador)

        return self._resultado("venta", comprador)

    def _siguiente_por_algoritmo(self):
        """Decide y desencola al siguiente comprador (None si todo está vacío)."""
        hay_prioritarios = not self.cola_prioridad.esta_vacia()
        hay_regulares = not self.cola_regular.esta_vacia()

        # Solo hay prioritarios: se atiende prioridad.
        if hay_prioritarios and not hay_regulares:
            self._prioritarios_consecutivos += 1
            return self.cola_prioridad.desencolar()

        # Cola de prioridad vacía: se atiende solo a la regular.
        if not hay_prioritarios:
            if not hay_regulares:
                return None
            self._prioritarios_consecutivos = 0
            return self.cola_regular.desencolar()

        # Ambas filas tienen gente -> se aplica la regla 3:1.
        if self._prioritarios_consecutivos < self.RATIO_PRIORITARIOS_POR_REGULAR:
            self._prioritarios_consecutivos += 1
            return self.cola_prioridad.desencolar()

        self._prioritarios_consecutivos = 0
        return self.cola_regular.desencolar()

    # ------------------------------------------------------------------
    # Consultas y simulación
    # ------------------------------------------------------------------
    def estado_filas(self):
        """Devuelve un resumen de ambas filas sin extraer compradores."""
        lineas = [
            "===== ESTADO DE LAS FILAS =====",
            f"Entradas restantes: {self.entradas_restantes} / {self.total_entradas}",
            f"Cola Regular:      {len(self.cola_regular)} esperando",
            f"Cola de Prioridad: {len(self.cola_prioridad)} esperando",
        ]
        if not self.cola_regular.esta_vacia():
            lineas.append(f"  Siguiente regular -> {self.cola_regular.ver_frente()}")
        if not self.cola_prioridad.esta_vacia():
            lineas.append(f"  Siguiente prioritario -> {self.cola_prioridad.ver_frente()}")
        if self.cola_regular.esta_vacia() and self.cola_prioridad.esta_vacia():
            lineas.append("  Ambas filas están vacías.")
        return "\n".join(lineas)

    def simular_masiva(self, cantidad=50):
        """Auto-genera y encola N compradores aleatorios (bonus)."""
        if self.sold_out:
            return 0, 0
        generados, encolados = 0, 0
        for _ in range(cantidad):
            comprador = _generar_comprador_aleatorio()
            generados += 1
            try:
                self.registrar_comprador(comprador)
                encolados += 1
            except ValueError:
                break  # SOLD OUT a mitad de la simulación
        return generados, encolados

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------
    def _vaciar_colas(self):
        self.cola_regular.vaciar()
        self.cola_prioridad.vaciar()

    def _resultado(self, tipo, comprador=None):
        return {
            "tipo": tipo,
            "comprador": comprador,
            "restantes": self.entradas_restantes,
            "sold_out": self.sold_out,
        }