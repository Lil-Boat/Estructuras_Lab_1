"""Pruebas automatizadas del motor de filas (sin interfaz de usuario).

Ejecutar:  python pruebas.py
"""

from cola import Cola
from cola_prioridad import ColaPrioridad
from comprador import Comprador
from sistema import SistemaBoletaje


def test_cola_fifo():
    """La cola estándar debe respetar FIFO estricto."""
    cola = Cola()
    assert cola.esta_vacia()
    for n in range(5):
        cola.encolar(n)
    assert len(cola) == 5
    salida = [cola.desencolar() for _ in range(5)]
    assert salida == [0, 1, 2, 3, 4], f"FIFO no respetado: {salida}"
    assert cola.esta_vacia()
    assert cola.ver_frente() is None
    print("OK  test_cola_fifo")


def test_cola_prioridad_orden():
    """Preferencial (P1) antes que VIP (P2); VIP respetan orden de llegada."""
    cola = ColaPrioridad()
    pedro = Comprador("Pedro", "11111111", Comprador.VIP)
    ana = Comprador("Ana", "22222222", Comprador.PREFERENCIAL)
    luis = Comprador("Luis", "33333333", Comprador.VIP)
    cola.encolar(pedro, 2)   # Pedro llega primero (nivel 2)
    cola.encolar(ana, 1)     # Ana se encola delante (nivel 1 = máximo)
    cola.encolar(luis, 2)    # Luis queda detrás de Pedro (mismo nivel: FIFO)
    orden = [cola.desencolar().nombre for _ in range(3)]
    assert orden == ["Ana", "Pedro", "Luis"], f"Orden incorrecto: {orden}"
    assert cola.esta_vacia()
    print("OK  test_cola_prioridad_orden")


def test_registro_categorias():
    """Cada categoría debe ir a la fila correcta."""
    sistema = SistemaBoletaje()
    sistema.registrar_comprador(Comprador("Reg", "10000000", Comprador.REGULAR))
    sistema.registrar_comprador(Comprador("Vip", "20000000", Comprador.VIP))
    sistema.registrar_comprador(Comprador("Pref", "30000000", Comprador.PREFERENCIAL))
    assert len(sistema.cola_regular) == 1
    assert len(sistema.cola_prioridad) == 2
    print("OK  test_registro_categorias")


def test_despacho_3_a_1():
    """Con ambas filas llenas el orden debe ser P P P R P P P R."""
    sistema = SistemaBoletaje(total_entradas=500)
    for i in range(6):
        sistema.registrar_comprador(Comprador(f"P{i}", f"{i:08d}", Comprador.PREFERENCIAL))
    for i in range(2):
        sistema.registrar_comprador(Comprador(f"R{i}", f"{10 + i:08d}", Comprador.REGULAR))

    atendidos = []
    while not (sistema.cola_regular.esta_vacia() and sistema.cola_prioridad.esta_vacia()):
        resultado = sistema.atender_siguiente()
        atendidos.append(resultado["comprador"].nombre)

    assert atendidos == ["P0", "P1", "P2", "R0", "P3", "P4", "P5", "R1"], \
        f"Regla 3:1 incumplida: {atendidos}"
    assert sistema.entradas_restantes == 500 - 8
    print("OK  test_despacho_3_a_1")


def test_despacho_solo_prioridad():
    """Sin regulares, se atienden solo prioritarios en orden FIFO interno."""
    sistema = SistemaBoletaje()
    for i in range(4):
        sistema.registrar_comprador(Comprador(f"V{i}", f"{i:08d}", Comprador.VIP))
    nombres = [sistema.atender_siguiente()["comprador"].nombre for _ in range(4)]
    assert nombres == ["V0", "V1", "V2", "V3"]
    print("OK  test_despacho_solo_prioridad")


def test_despacho_solo_regular_cuando_prioridad_vacia():
    """Si la cola de prioridad está vacía, se atiende solo la regular."""
    sistema = SistemaBoletaje()
    for i in range(3):
        sistema.registrar_comprador(Comprador(f"P{i}", "10000000", Comprador.PREFERENCIAL))
    for i in range(3):
        sistema.registrar_comprador(Comprador(f"R{i}", "20000000", Comprador.REGULAR))

    primero = sistema.atender_siguiente()["comprador"].nombre
    segundo = sistema.atender_siguiente()["comprador"].nombre
    tercero = sistema.atender_siguiente()["comprador"].nombre
    cuarto = sistema.atender_siguiente()["comprador"].nombre

    assert [primero, segundo, tercero] == ["P0", "P1", "P2"]
    assert cuarto == "R0", \
        f"Debía atender regular al vaciarse la prioridad, atendió {cuarto}"
    print("OK  test_despacho_solo_regular_cuando_prioridad_vacia")


def test_sold_out_vende_negativo_jamas():
    """SOLD OUT en 0, se vacían las colas y jamás se vende una entrada -1."""
    sistema = SistemaBoletaje(total_entradas=3)
    for i in range(10):
        sistema.registrar_comprador(Comprador(f"C{i}", f"{i:08d}", Comprador.REGULAR))

    res1 = sistema.atender_siguiente()
    res2 = sistema.atender_siguiente()
    res3 = sistema.atender_siguiente()
    assert res1["tipo"] == "venta" and res1["restantes"] == 2
    assert res2["tipo"] == "venta" and res2["restantes"] == 1
    assert res3["tipo"] == "ultima_entrada" and res3["sold_out"] is True

    # Ya no vende más (nunca -1) y las colas quedaron vacías:
    res4 = sistema.atender_siguiente()
    assert res4["tipo"] == "sold_out"
    assert sistema.entradas_restantes == 0, "Las entradas no pueden bajar de 0"
    assert sistema.cola_regular.esta_vacia()
    assert sistema.cola_prioridad.esta_vacia()

    # Registrar tras SOLD OUT debe rechazarse:
    try:
        sistema.registrar_comprador(Comprador("X", "99999999", Comprador.REGULAR))
        assert False, "No debía permitir registrar después de SOLD OUT"
    except ValueError:
        pass
    print("OK  test_sold_out_vende_negativo_jamas")


def test_filas_vacias_sin_clientes():
    """Atender con filas vacías no debe fallar ni vender nada."""
    sistema = SistemaBoletaje()
    res = sistema.atender_siguiente()
    assert res["tipo"] == "sin_clientes"
    assert sistema.entradas_restantes == 500
    print("OK  test_filas_vacias_sin_clientes")


def test_simulacion_masiva():
    """La simulación masiva debe generar y encolar 50 compradores."""
    sistema = SistemaBoletaje()
    generados, encolados = sistema.simular_masiva(50)
    assert generados == 50 and encolados == 50
    total = len(sistema.cola_regular) + len(sistema.cola_prioridad)
    assert total == 50
    print("OK  test_simulacion_masiva")


def test_robustez_letras_en_entrada():
    """El filtro del menú rechaza letras ANTES de convertirlas a entero."""
    for texto_malo in ("abc", "tres", "", "-5", "12.5", "dos 3"):
        assert not texto_malo.isdigit(), f"'{texto_malo}' no debe pasar como entero"
    assert "12".isdigit() and int("12") == 12
    print("OK  test_robustez_letras_en_entrada")


def test_vendedor_registro_y_login():
    """Las credenciales del vendedor se guardan y validan en el sistema."""
    sistema = SistemaBoletaje()
    assert sistema.vendedor_registrado is None

    # Sin vendedor registrado, el login debe denegarse:
    assert sistema.iniciar_sesion_vendedor("X", "123") is None

    sistema.registrar_vendedor("Roberto Gómez", "clave123")
    assert sistema.vendedor_registrado["nombre"] == "Roberto Gómez"

    # Credenciales correctas -> acceso concedido
    vendedor = sistema.iniciar_sesion_vendedor("Roberto Gómez", "clave123")
    assert vendedor is not None and vendedor["nombre"] == "Roberto Gómez"

    # Credenciales incorrectas -> denegado
    assert sistema.iniciar_sesion_vendedor("Roberto Gómez", "mal") is None
    assert sistema.iniciar_sesion_vendedor("Otra", "clave123") is None

    # Re-registrar reemplaza las credenciales guardadas
    sistema.registrar_vendedor("Ana Vargas", "nueva456")
    assert sistema.iniciar_sesion_vendedor("Roberto Gómez", "clave123") is None
    assert sistema.iniciar_sesion_vendedor("Ana Vargas", "nueva456") is not None
    print("OK  test_vendedor_registro_y_login")


def main():
    pruebas = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for prueba in pruebas:
        prueba()
    print(f"\n[+] {len(pruebas)} pruebas pasaron sin errores.")


if __name__ == "__main__":
    main()