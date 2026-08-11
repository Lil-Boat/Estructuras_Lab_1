# Ticket UNA — Sistema de Boletaje de Alta Demanda

Prototipo de **fila virtual** para la licitación de emergencia: gestiona la
venta de **500 entradas** usando **Colas (FIFO)** y **Colas de Prioridad**
construidas desde cero con **nodos enlazados** (TDA). No usa listas ni
arreglos para simular las filas.

## Requisitos

- Python 3.10 o superior (probado con Python 3.13).

## Cómo ejecutar

```bash
python main.py          # menú interactivo (requiere una terminal interactiva)
python pruebas.py       # suite de pruebas lógicas
python pruebas_main.py  # pruebas de integración del menú (entrada simulada)
```

> **Importante**: el menú lee del **teclado**. El programa hace una doble
> verificación al iniciar:
> 1. Si la entrada está **redirigida** (tubería, runner sin consola) avisa y se
>    cierra, en lugar de "autocompletar" los campos con basura.
> 2. Si la terminal es interactiva pero **ya tenía texto cargado** (p. ej. un
>    *Dedicated Terminal* de VS Code reutilizado que dejó el comando anterior
>    en el buffer) avisa y se cierra.
>
> La solución en VS Code es cerrar esa terminal (ícono de la **papelera**),
> abrir una nueva y volver a ejecutar. En la parte de arriba de la pantalla se
> muestra el **build** del programa (p. ej. `build 2026-11-08`) para confirmar
> que se ejecuta la versión más reciente.
>
> Para pruebas automáticas por tubería use `$env:TICKET_UNA_PIPE = '1'`.

## Estructura del proyecto

| Archivo            | Responsabilidad                                            |
|--------------------|-----------------------------------------------------------|
| `nodo.py`          | TDA Nodo (dato + enlace al siguiente)                      |
| `cola.py`          | Cola estándar FIFO con nodos (encolar/desencolar O(1))     |
| `cola_prioridad.py`| Cola de prioridad con nodos (FIFO estable entre iguales)   |
| `comprador.py`     | Modelo de datos del comprador (categoría y prioridad)      |
| `sistema.py`       | Motor de filas, 500 entradas, SOLD OUT y cuentas del vendedor |
| `main.py`          | Menú de consola con roles, acceso del vendedor y validación total de entrada |
| `pruebas.py`       | Pruebas automatizadas de toda la lógica                    |
| `pruebas_main.py`  | Pruebas de integración del menú (roles y acceso)           |

## Reglas del motor de filas

1. **Regular** va a la **Cola FIFO**.
2. **Preferencial (Ley 7600)** va a la **Cola de Prioridad** con nivel **1** (máximo).
3. **VIP** va a la **Cola de Prioridad** con nivel **2**.
4. **Despacho 3:1**: se atienden 3 prioritarios por cada 1 regular → secuencia `P P P R P P P R ...`.
5. Si la cola de prioridad está **vacía**, se atiende solo a la regular.
6. Al llegar a **0** entradas → mensaje de **SOLD OUT** y se **vacían ambas filas**.
   El sistema jamás vende una entrada "-1".
7. **Reservas por comprador**: al registrarse, el comprador elige cuántas
   entradas reservar (**máx. 5 por usuario**). El contador baja **de inmediato**
   al reservar (el cupo queda apartado). Cuando el vendedor atiende, se
   entregan las entradas que ese comprador ya tenía reservadas, sin volver a
   descontar.

## Criterios de la competencia que se cumplen

- **First Blood**: el despacho 3:1 está implementado y cubierto por pruebas
  (`test_despacho_3_a_1`).
- **Cero Caídas**: toda entrada del usuario pasa por validación
  (`leer_entero` usa `isdigit`, cédulas y nombres validados). Escribir letras
  en el menú **nunca** rompe el programa.
- **Código Limpio (TDA)**: `Cola`, `ColaPrioridad` y `Nodo` están hechas con
  nodos enlazados; no hay `list`/arreglos simulando filas.
- **Manejo del Límite (Sold Out)**: al llegar a 0 la venta se detiene, las
  colas se vacían y cualquier intento posterior responde `SOLD OUT`.

## Roles y menús

Al iniciar, el programa pregunta el rol del usuario:

```
=== ¿Con qué rol desea ingresar? ===
  1. Vendedor  -> opera el sistema de boletaje
  2. Comprador -> compra su entrada y consulta el estado
  3. Salir del programa
```

### Desplazarse entre roles

Las opciones de salida de ambos menús **vuelven a la selección de rol**,
así se puede alternar entre vendedor y comprador sin reiniciar el programa
y hacer pruebas con las mismas filas en memoria.

### Flujo del Vendedor

Al elegir "Vendedor" aparece un **sub-menú de acceso** con dos opciones:

```
=== ACCESO DEL VENDEDOR ===
1. Registrar vendedor (nombre y contraseña)  <- las credenciales se guardan en el sistema
2. Ingresar como vendedor (credenciales guardadas)
3. Volver a la selección de rol
```

La primera vez que se entra como vendedor se **registra** la cuenta (nombre y
contraseña), que queda guardada en el sistema. Si luego se pasa al menú del
comprador y se vuelve a "Vendedor", se elige la opción 2 e **ingresa con las
credenciales ya guardadas**. Una vez autenticado se muestra el **menú del
vendedor** con las opciones originales:

```
1. Registrar comprador en fila
2. Atender siguiente comprador
3. Mostrar estado de las filas        <- aquí ve las solicitudes pendientes
4. Simulación masiva (50 compradores)  <- bonus
5. Volver a la selección de rol
```

### Flujo del Comprador

El comprador puede **registrarse reservando entradas** (nombre, cédula,
categoría y **cantidad: 1 a 5 entradas**) y consultar el estado de las filas:

```
1. Registrarme en la fila         <- elige cuántas entradas reservar (máx. 5)
2. Mostrar estado de las filas
3. Volver a la selección de rol
```

Al reservar, el contador de entradas disponibles baja de inmediato con la
cantidad elegida.

## Complejidad (con nodos enlazados)

| Operación                     | Costo       |
|-------------------------------|-------------|
| Encolar Cola (FIFO)           | O(1)        |
| Desencolar Cola (FIFO)        | O(1)        |
| Encolar Cola de Prioridad     | O(n) peor caso |
| Desencolar Cola de Prioridad  | O(1)        |
| Despacho 3:1 (decisión)       | O(1)        |
| Memoria total                 | O(n)        |

## Ejemplo de ejecución (recorte)

```
=== MENÚ PRINCIPAL | Entradas restantes: 500 ===
  1. Registrar comprador en fila
  ...
  Opción [1-5]: 4

--- Simulación masiva: 50 compradores aleatorios ---
  [+] Compradores generados: 50 | Encolados: 50

===== ESTADO DE LAS FILAS =====
Entradas restantes: 500 / 500
Cola Regular:      25 esperando
Cola de Prioridad: 25 esperando
  Siguiente regular -> ...
  Siguiente prioritario -> ...
```