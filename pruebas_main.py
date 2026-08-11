"""Pruebas de integración del menú (roles y acceso del vendedor).

Simulan la entrada del usuario sustituyendo builtins.input por respuestas
pre-cargadas, así no depende de una terminal interactiva ni de tuberías.

Ejecutar:  python pruebas_main.py
"""

import builtins
import os
import sys

import main as main_mod
from comprador import Comprador
from sistema import SistemaBoletaje


class SimuladorEntrada:
    """Sustituye a input() devolviendo respuestas pre-cargadas, en orden."""

    def __init__(self, respuestas):
        self.pendientes = list(respuestas)
        self.registro = []  # (mensaje, valor) ya consumidos
        self._original = builtins.input

    def entrar(self):
        builtins.input = self._falso_input

    def salir(self):
        builtins.input = self._original

    def _falso_input(self, mensaje=""):
        if not self.pendientes:
            raise AssertionError(
                f"El menú pidió más entradas de las simuladas. "
                f"Último prompt: '{mensaje}'")
        valor = self.pendientes.pop(0)
        self.registro.append((mensaje, valor))
        return valor


def test_elegir_rol_opciones():
    """La selección de rol responde 'vendedor', 'comprador' o 'salir'."""
    casos = {"1": "vendedor", "2": "comprador", "3": "salir"}
    for opcion, esperado in casos.items():
        simulador = SimuladorEntrada([opcion])
        simulador.entrar()
        try:
            assert main_mod.elegir_rol() == esperado
        finally:
            simulador.salir()
    print("OK  test_elegir_rol_opciones")


def test_flujo_acceso_vendedor_completo():
    """Registrar vendedor y luego ingresar con las credenciales guardadas."""
    sistema = SistemaBoletaje()
    respuestas = [
        "1",              # acceso: registrar vendedor
        "Roberto Gómez",  # nombre
        "clave123",       # contraseña
        "",               # [ENTER]
        "2",              # acceso: ingresar como vendedor
        "Roberto Gómez",  # nombre
        "clave123",       # contraseña -> acceso concedido
        "5",              # menú del vendedor: volver a la selección de rol
    ]
    simulador = SimuladorEntrada(respuestas)
    simulador.entrar()
    try:
        main_mod.menu_vendedor_acceso(sistema)
    finally:
        simulador.salir()

    assert sistema.vendedor_registrado == {
        "nombre": "Roberto Gómez", "contrasena": "clave123"}
    assert not simulador.pendientes, "debió consumirse toda la entrada"
    print("OK  test_flujo_acceso_vendedor_completo")


def test_flujo_acceso_credenciales_incorrectas():
    """La contraseña equivocada NO da acceso y no entra al menú."""
    sistema = SistemaBoletaje()
    sistema.registrar_vendedor("Ana Vargas", "correcta")
    respuestas = [
        "2",             # acceso: ingresar
        "Ana Vargas",    # nombre
        "incorrecta",    # contraseña INCORRECTA
        "",              # [ENTER]
        "3",             # volver a la selección de rol
    ]
    simulador = SimuladorEntrada(respuestas)
    simulador.entrar()
    try:
        main_mod.menu_vendedor_acceso(sistema)
    finally:
        simulador.salir()
    assert not simulador.pendientes
    assert sistema.entradas_restantes == 500  # nada se vendió ni se corrompió
    print("OK  test_flujo_acceso_credenciales_incorrectas")


def test_flujo_sin_vendedor_registrado():
    """Ingresar sin vendedor registrado avisa y no pide credenciales."""
    sistema = SistemaBoletaje()
    respuestas = ["2", "", "3"]
    simulador = SimuladorEntrada(respuestas)
    simulador.entrar()
    try:
        main_mod.menu_vendedor_acceso(sistema)
    finally:
        simulador.salir()
    assert not simulador.pendientes
    print("OK  test_flujo_sin_vendedor_registrado")


def test_menu_vendedor_atiende_entrada():
    """La opción 2 del menú del vendedor sirve una entrada y descuenta 1."""
    sistema = SistemaBoletaje()
    sistema.registrar_comprador(Comprador("Pepe", "10101010", Comprador.REGULAR))
    respuestas = ["2", "", "5"]   # atender, [ENTER], volver
    simulador = SimuladorEntrada(respuestas)
    simulador.entrar()
    try:
        main_mod.menu_vendedor(sistema, {"nombre": "Ana", "contrasena": "x"})
    finally:
        simulador.salir()
    assert sistema.entradas_restantes == 499
    assert sistema.cola_regular.esta_vacia()
    assert not simulador.pendientes
    print("OK  test_menu_vendedor_atiende_entrada")


def test_registrar_vendedor_ya_existente():
    """Si ya hay vendedor, pedir registro de nuevo pide confirmación."""
    sistema = SistemaBoletaje()
    sistema.registrar_vendedor("Cuenta Vieja", "clavevieja")
    respuestas = ["2", "", "1", "Cuenta Nueva", "clavenueva"]
    # 1) registrar: como ya existe, pregunta "1 = Sí / 2 = No" -> "2" (No),
    #    se mantiene la cuenta actual.
    # 2) [ENTER]
    # 3) registrar de nuevo -> "1" (Sí): reemplaza la cuenta.
    simulador = SimuladorEntrada(respuestas)
    simulador.entrar()
    try:
        main_mod.registrar_vendedor(sistema)
        main_mod.registrar_vendedor(sistema)
    finally:
        simulador.salir()
    assert sistema.vendedor_registrado == {
        "nombre": "Cuenta Nueva", "contrasena": "clavenueva"}
    assert not simulador.pendientes
    print("OK  test_registrar_vendedor_ya_existente")


def test_verificar_terminal():
    """La guardia cubre: tubería, tubería+flag, teclado limpio y buffer sucio."""
    original_stdin = sys.stdin
    original_pendiente = main_mod._hay_entrada_pendiente

    no_tty = type("FakeStdin", (), {"isatty": lambda self: False})()
    es_tty = type("FakeTty", (), {"isatty": lambda self: True})()

    try:
        # stdin NO interactivo y sin flag -> se niega
        sys.stdin = no_tty
        main_mod._hay_entrada_pendiente = lambda: False
        os.environ.pop("TICKET_UNA_PIPE", None)
        assert main_mod._verificar_terminal() is False

        # stdin NO interactivo pero con flag de pruebas -> permite
        os.environ["TICKET_UNA_PIPE"] = "1"
        assert main_mod._verificar_terminal() is True
        del os.environ["TICKET_UNA_PIPE"]

        # stdin interactivo y buffer limpio -> permite (teclado normal)
        sys.stdin = es_tty
        assert main_mod._verificar_terminal() is True

        # stdin interactivo pero con texto ya cargado -> se niega
        main_mod._hay_entrada_pendiente = lambda: True
        assert main_mod._verificar_terminal() is False

        # buffer sucio pero con flag de pruebas -> permite
        os.environ["TICKET_UNA_PIPE"] = "1"
        assert main_mod._verificar_terminal() is True
        del os.environ["TICKET_UNA_PIPE"]
    finally:
        sys.stdin = original_stdin
        main_mod._hay_entrada_pendiente = original_pendiente
    print("OK  test_verificar_terminal")


def test_registrar_comprador_con_cantidad():
    """El comprador elige cuántas entradas reservar y el contador baja."""
    sistema = SistemaBoletaje()
    respuestas = [
        "1",              # menú comprador: registrarme en la fila
        "Ana Pérez",      # nombre
        "987654321",      # cédula
        "3",              # categoría: Preferencial (Ley 7600)
        "3",              # cantidad: 3 entradas
        "",               # [ENTER]
        "2",              # menú comprador: estado de filas
        "",               # [ENTER]
        "3",              # menú comprador: volver a la selección de rol
    ]
    simulador = SimuladorEntrada(respuestas)
    simulador.entrar()
    try:
        main_mod.menu_comprador(sistema)
    finally:
        simulador.salir()
    assert sistema.entradas_restantes == 500 - 3
    assert len(sistema.cola_prioridad) == 1
    assert sistema.cola_prioridad.ver_frente().cantidad == 3
    assert not simulador.pendientes
    print("OK  test_registrar_comprador_con_cantidad")


def main():
    pruebas = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for prueba in pruebas:
        prueba()
    print(f"\n[+] {len(pruebas)} pruebas de integración pasaron sin errores.")


if __name__ == "__main__":
    main()