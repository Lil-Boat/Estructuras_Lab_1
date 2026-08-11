"""Ticket UNA - Sistema de Boletaje de Alta Demanda (punto de entrada).

Menú de consola. Todas las entradas del usuario se validan antes de usarse,
de modo que escribir letras o símbolos nunca tumba el programa (Cero Caídas).

Ejecutar:  python main.py
"""

import os
import sys

# Asegura que la consola (incluso redirigida a un pipe) nunca falle al
# imprimir acentos o símbolos -> clave para el criterio "Cero Caídas".
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from comprador import Comprador
from sistema import SistemaBoletaje

_CATEGORIAS = (Comprador.REGULAR, Comprador.VIP, Comprador.PREFERENCIAL)


def leer_entero(mensaje, minimo=None, maximo=None):
    """Lee un entero validado; reintenta si el usuario escribe letras."""
    while True:
        texto = input(mensaje).strip()
        if not texto.isdigit():
            print("  [!] Entrada inválida: debe escribir un número entero.")
            continue
        valor = int(texto)
        if minimo is not None and valor < minimo:
            print(f"  [!] El número debe ser mayor o igual a {minimo}.")
            continue
        if maximo is not None and valor > maximo:
            print(f"  [!] El número debe ser menor o igual a {maximo}.")
            continue
        return valor


def leer_texto_no_vacio(mensaje):
    """Lee un texto que no puede quedar vacío."""
    while True:
        texto = input(mensaje).strip()
        if texto:
            return texto
        print("  [!] El campo no puede quedar vacío.")


def leer_cedula(mensaje):
    """Lee una cédula numérica válida (solo dígitos, 5+ caracteres)."""
    while True:
        texto = input(mensaje).strip()
        if texto.isdigit() and len(texto) >= 5:
            return texto
        print("  [!] La cédula debe contener solo números (mínimo 5 dígitos).")


def _verificar_terminal():
    """Detecta si el programa tiene una terminal interactiva real.

    Si se ejecuta con stdin redirigido (tubería, archivo, runner sin consola),
    input() NO espera al teclado: lee basura de la tubería y el menú se
    "autocompleta" solo (p. ej. rellena el nombre con la ruta del proyecto).
    En ese caso se avisa y se sale con un error claro en vez de corromper datos.

    Excepción: con la variable de entorno TICKET_UNA_PIPE=1 se permite el modo
    por tubería, pensado para pruebas automáticas.
    """
    if sys.stdin.isatty():
        return True
    if os.environ.get("TICKET_UNA_PIPE") == "1":
        return True
    ancho = 58
    print("=" * ancho)
    print("  [!] No se detectó una terminal interactiva.")
    print()
    print("      Este programa lee del teclado y NO debe recibir datos")
    print("      por tubería ni redirección. Ejecútelo directamente:")
    print()
    print("          python main.py")
    print()
    print("      (Para pruebas automáticas:  $env:TICKET_UNA_PIPE='1')")
    print("=" * ancho)
    return False


def _bienvenida(sistema):
    ancho = 58
    print("=" * ancho)
    print("  TICKET UNA - Sistema de Boletaje de Alta Demanda")
    print(f"  Concierto de la Década | {sistema.total_entradas} entradas disponibles")
    print("=" * ancho)


def _mostrar_menu_vendedor(sistema):
    if sistema.sold_out:
        estado = "SOLD OUT"
    else:
        estado = f"Entradas restantes: {sistema.entradas_restantes}"
    print(f"\n=== MENÚ DEL VENDEDOR | {estado} ===")
    print("  1. Registrar comprador en fila")
    print("  2. Atender siguiente comprador")
    print("  3. Mostrar estado de las filas")
    print("  4. Simulación masiva (50 compradores)")
    print("  5. Volver a la selección de rol")


def registrar_comprador(sistema):
    print("\n--- Registrar comprador en fila ---")
    nombre = leer_texto_no_vacio("  Nombre completo: ")
    cedula = leer_cedula("  Cédula: ")
    print("  Categoría del tiquete:")
    print("    1. Regular (fila normal)")
    print("    2. VIP (membresía anual)")
    print("    3. Preferencial (Ley 7600: adulto mayor, embarazada, discapacidad)")
    opcion = leer_entero("  Seleccione [1-3]: ", 1, 3)
    categoria = _CATEGORIAS[opcion - 1]
    comprador = Comprador(nombre, cedula, categoria)
    try:
        sistema.registrar_comprador(comprador)
    except ValueError as error:
        print(f"  [!] {error}")
        return
    fila = "Prioridad" if comprador.es_prioritario else "Regular"
    print(f"  [+] {comprador.nombre} encolado en la Fila {fila} (categoría: {categoria}).")


def atender_siguiente(sistema):
    print("\n--- Atender siguiente comprador ---")
    resultado = sistema.atender_siguiente()
    tipo = resultado["tipo"]
    if tipo == "sin_clientes":
        print("  Las filas están vacías: no hay compradores que atender.")
    elif tipo == "venta":
        c = resultado["comprador"]
        print(f"  Entrada vendida a {c.nombre} - Categoría: {c.categoria}. "
              f"Entradas restantes: {resultado['restantes']}.")
    elif tipo == "ultima_entrada":
        c = resultado["comprador"]
        print(f"  Entrada vendida a {c.nombre} - Categoría: {c.categoria}. Entradas restantes: 0.")
        print("  [!!] SOLD OUT - Todas las entradas se agotaron. Las filas se vaciaron.")
    elif tipo == "sold_out":
        print("  [!] SOLD OUT - La venta está cerrada: no quedan entradas.")


def mostrar_estado(sistema):
    print("\n" + sistema.estado_filas())


def simulacion_masiva(sistema):
    print("\n--- Simulación masiva: 50 compradores aleatorios ---")
    if sistema.sold_out:
        print("  [!] SOLD OUT: la venta está cerrada, no se puede simular.")
        return
    generados, encolados = sistema.simular_masiva(50)
    print(f"  [+] Compradores generados: {generados} | Encolados: {encolados}")
    print(sistema.estado_filas())


def elegir_rol():
    """Pantalla de ingreso: elige rol (para desplazarse entre ellos) o sale."""
    print("\n=== ¿Con qué rol desea ingresar? ===")
    print("  1. Vendedor  -> opera el sistema de boletaje (registra, atiende, ve las solicitudes)")
    print("  2. Comprador -> compra su entrada y consulta el estado de las filas")
    print("  3. Salir del programa")
    opcion = leer_entero("  Seleccione [1-3]: ", 1, 3)
    if opcion == 1:
        return "vendedor"
    if opcion == 2:
        return "comprador"
    return "salir"


def registrar_vendedor(sistema):
    """Registra una cuenta de vendedor en el sistema (nombre + contraseña)."""
    print("\n--- Registrar Vendedor (nueva cuenta) ---")
    if sistema.vendedor_registrado:
        print("  [!] Ya existe un vendedor registrado.")
        opcion = leer_entero(
            "  ¿Desea reemplazarlo por uno nuevo? (1 = Sí, 2 = No): ", 1, 2)
        if opcion == 2:
            print("  Cancelado: se mantiene el vendedor actual.")
            return
    nombre = leer_texto_no_vacio("  Nombre completo: ")
    contrasena = leer_texto_no_vacio("  Contraseña: ")
    sistema.registrar_vendedor(nombre, contrasena)
    print(f"  [+] Vendedor '{nombre}' registrado correctamente. Ya puede iniciar sesión.")


def iniciar_sesion_vendedor(sistema):
    """Ingresa con las credenciales guardadas. Devuelve el vendedor o None."""
    print("\n--- Ingresar como Vendedor ---")
    if sistema.vendedor_registrado is None:
        print("  [!] No hay vendedores registrados. Use primero la opción 1.")
        return None
    nombre = leer_texto_no_vacio("  Nombre completo: ")
    contrasena = leer_texto_no_vacio("  Contraseña: ")
    vendedor = sistema.iniciar_sesion_vendedor(nombre, contrasena)
    if vendedor is None:
        print("  [!] Credenciales incorrectas: nombre o contraseña inválidos.")
        return None
    print(f"  [+] Acceso concedido. Bienvenido, {vendedor['nombre']}.")
    return vendedor


def menu_vendedor_acceso(sistema):
    """Sub-menú del vendedor: registrar cuenta o iniciar sesión."""
    while True:
        print("\n=== ACCESO DEL VENDEDOR ===")
        print("  1. Registrar vendedor (nombre y contraseña)")
        print("  2. Ingresar como vendedor (credenciales guardadas)")
        print("  3. Volver a la selección de rol")
        opcion = leer_entero("  Opción [1-3]: ", 1, 3)
        if opcion == 1:
            registrar_vendedor(sistema)
        elif opcion == 2:
            vendedor = iniciar_sesion_vendedor(sistema)
            if vendedor is not None:
                menu_vendedor(sistema, vendedor)
                return
        else:
            print("\n  Volviendo a la selección de rol...")
            return
        input("  [ENTER] para continuar...")


def menu_vendedor(sistema, vendedor):
    """Flujo del vendedor: mismas opciones del sistema original."""
    print(f"\n  [VENDEDOR] {vendedor['nombre']} - Sistema de boletaje activo.")
    while True:
        _mostrar_menu_vendedor(sistema)
        opcion = leer_entero("  Opción [1-5]: ", 1, 5)
        if opcion == 1:
            registrar_comprador(sistema)
        elif opcion == 2:
            atender_siguiente(sistema)
        elif opcion == 3:
            mostrar_estado(sistema)   # aquí el vendedor ve las solicitudes pendientes
        elif opcion == 4:
            simulacion_masiva(sistema)
        else:
            print("\n  Volviendo a la selección de rol...")
            break
        input("  [ENTER] para continuar...")


def menu_comprador(sistema):
    """Flujo del comprador: registrarse en la fila y consultar el estado."""
    while True:
        print("\n=== MENÚ DEL COMPRADOR ===")
        print("  1. Registrarme en la fila")
        print("  2. Mostrar estado de las filas")
        print("  3. Volver a la selección de rol")
        opcion = leer_entero("  Opción [1-3]: ", 1, 3)
        if opcion == 1:
            registrar_comprador(sistema)
        elif opcion == 2:
            mostrar_estado(sistema)
        else:
            print("\n  Volviendo a la selección de rol...")
            break
        input("  [ENTER] para continuar...")


def main():
    try:
        if not _verificar_terminal():
            sys.exit(1)
        sistema = SistemaBoletaje()
        _bienvenida(sistema)
        while True:
            rol = elegir_rol()
            if rol == "vendedor":
                menu_vendedor_acceso(sistema)
            elif rol == "comprador":
                menu_comprador(sistema)
            else:
                print("\n  Gracias por usar Ticket UNA. ¡Hasta la próxima función!")
                break
    except (KeyboardInterrupt, EOFError):
        print("\n  Sesión finalizada.")


if __name__ == "__main__":
    main()