# Calibrate

Sistema de reservas de equipos de laboratorio por consola (Python 3 + SQLite).

## 1. Especificación

### 1.1 Problema y objetivo
**Problema.** La coordinación de un laboratorio registra los pedidos de equipos en mensajes y una planilla. A veces se confirma la misma unidad para horarios superpuestos, y otras veces una cancelación sigue bloqueando el horario. Hace falta consultar disponibilidad, reservar y cancelar sin perder el historial. El inventario ya está definido y cada ID identifica una unidad física distinta.

**Objetivo.** Reservar unidades de equipos de laboratorio por franjas horarias, sin superposiciones, y poder consultar disponibilidad y cancelar. Interfaz de consola; los datos persisten entre ejecuciones.

### 1.2 Conceptos
- **Unidad**: un equipo reservable con ID único (`MIC-01`, `MIC-02`, `OSC-01`, `MUL-01`, `FUE-01`), cargado desde `inventory.json`.
- **Reserva**: unidad + solicitante + inicio + fin + estado (`ACTIVE` o `CANCELLED`).
- **Solicitante**: texto libre (nombres ficticios en ejemplos y pruebas).

### 1.3 Reglas
| ID | Regla |
|---|---|
| R1 | Fecha y hora con formato `YYYY-MM-DD HH:MM`, hora de 24 h, fecha de calendario válida (30 de febrero y 25:00 se rechazan). |
| R2 | Una única zona horaria fija del laboratorio (America/Argentina/Buenos_Aires); no hay conversión. |
| R3 | Los intervalos son semiabiertos `[inicio, fin)`: 10:00-11:00 y 11:00-12:00 **no** chocan. |
| R4 | Dos reservas chocan si son de la **misma unidad**, ambas `ACTIVE`, y `a.inicio < b.fin` y `b.inicio < a.fin`. |
| R5 | Unidades distintas nunca chocan entre sí (MIC-02 se puede reservar con MIC-01 ocupado). |
| R6 | `inicio < fin` estrictamente. |
| R7 | El inicio no puede estar en el pasado (respecto al reloj actual). |
| R8 | Duración máxima: 8 h (exactamente 8 h se acepta; 8 h 1 min se rechaza). |
| R9 | Anticipación máxima: 90 días desde ahora para el inicio (exactamente 90 días se acepta; más, se rechaza). |
| R10 | La unidad debe existir. |
| R11 | El solicitante no puede estar vacío ni contener solo espacios; se guarda sin espacios en los extremos. |
| R12 | Cancelar cambia el estado a `CANCELLED` y registra `cancelled_at`; **no borra** el registro. Una reserva cancelada no bloquea la franja. |
| R13 | Cancelar una reserva ya cancelada o con ID inexistente da un error claro; nunca éxito silencioso. |
| R14 | La disponibilidad usa exactamente la misma función de choque (R4) que la reserva. |
| R15 | La comprobación de choque y la inserción ocurren en una sola transacción. |

### 1.4 Comandos
| Comando | Qué hace |
|---|---|
| `init` | Crea la base si no existe y agrega las unidades faltantes de `inventory.json`. Idempotente. |
| `reset --yes` | Borra **todas** las reservas (activas y canceladas) y vuelve a sembrar las unidades faltantes. Nunca borra unidades. Sin `--yes` no hace nada y avisa. |
| `units` | Lista las unidades. |
| `book --unit U --requester R --start S --end E` | Crea una reserva `ACTIVE` y muestra su ID. |
| `cancel --id N` | Cancela la reserva N. |
| `availability --start S --end E [--unit U]` | Con `--unit`: dice si esa unidad está libre y, si no, qué reservas la bloquean. Sin `--unit`: lista las unidades libres en ese intervalo. Valida el intervalo con las mismas reglas R1, R6 y R8. |
| `list [--unit U] [--all]` | Lista reservas `ACTIVE`; con `--all` incluye las canceladas. |

### 1.5 Errores
- Todo error de validación imprime un mensaje claro en español por stderr y termina con código de salida distinto de 0.
- Un comando fallido no modifica la base de datos.
- Éxito: código de salida 0.

### 1.6 Almacenamiento
SQLite en `data/calibrate.db` (ignorado por git); la variable de entorno `CALIBRATE_DB` permite usar otro archivo. Tablas: `units(id, name)` y `reservations(id, unit_id, requester, start, end, status, created_at, cancelled_at)`; `status` restringido a `ACTIVE` / `CANCELLED`.

### 1.7 Criterios de aceptación
1. Reservar MIC-01 de 10:00 a 11:00 en una fecha futura válida crea una reserva `ACTIVE`.
2. Reservar MIC-01 de 10:30 a 11:30 con la anterior activa se rechaza.
3. Reservar MIC-01 de 11:00 a 12:00 con la anterior activa se acepta.
4. Reservar MIC-02 de 10:00 a 11:00 con MIC-01 ocupado se acepta.
5. Se rechazan: unidad inexistente, solicitante `"   "`, 30 de febrero, hora 25:00, inicio >= fin, fecha pasada, duración > 8 h, anticipación > 90 días.
6. Cancelar conserva el registro (visible con `list --all`) y libera la franja para reservar de nuevo.
7. `availability` y `book` coinciden siempre: si `availability` dice libre, `book` acepta; si dice ocupada, `book` rechaza.
8. Dos ejecuciones separadas de la CLI ven las mismas reservas activas y canceladas.
9. Cancelar dos veces la misma reserva, o un ID inexistente, da error.
10. `init` repetido no duplica unidades; `reset` sin `--yes` no borra nada.

### 1.8 Fuera de alcance
Usuarios concurrentes en máquinas distintas, autenticación, varias zonas horarias, administración del inventario desde la CLI, reservas recurrentes.

### 1.9 Supuestos
Marcados como supuestos en `docs/PLAN.md` sección 1: idioma español, zona fija, límites de 8 h y 90 días. Se cambian solo con un commit de especificación aparte que explique el motivo.

### 1.10 Historial de la especificación
- `62e4191` («Spec inicial»): versión inicial, reglas R1-R15, comandos y criterios de aceptación.
- `4067a86`: se agregó a 1.6 la variable `CALIBRATE_DB`. Motivo: las pruebas de la CLI necesitan una base temporal sin tocar `data/calibrate.db`. Este cambio quedó dentro de un commit de evidencia, sin mención en su mensaje; se declara aquí para que sea recuperable.
- Cambio posterior a `9610f20`: 1.1 pasó a incluir el problema de negocio, que el enunciado pide y la versión inicial no tenía. No cambia ninguna regla.

## 2. Solución

### 2.1 Arquitectura
```
cli.py  ->  service.py  ->  domain.py       (reglas puras, sin I/O)
                        ->  repository.py -> SQLite
```
- `domain.py`: validación de fechas, intervalos y solicitante, y la **única** función de choque `overlaps` (`a.inicio < b.fin and b.inicio < a.fin`). La usan `book` y la consulta de disponibilidad (`blocking`, `free_units`), así que no pueden contradecirse.
- `repository.py`: SQL y transacciones. `book` toma el bloqueo de escritura (`BEGIN IMMEDIATE`) antes de comprobar y insertar.
- `service.py`: casos de uso (`init`, `reset`, `book`, `cancel`, `list`, `blocking`, `free_units`). El reloj se inyecta (`now=`) para pruebas deterministas.
- `cli.py`: capa fina de `argparse`; los errores van a stderr con código de salida 1.

### 2.2 Requisitos previos, instalación y uso
**Requisitos previos y versiones.** Python **3.10 o superior** (probado con 3.10.11) y `pytest==9.1.1` (fijado en `requirements.txt`). El resto es biblioteca estándar (`sqlite3`, `argparse`). No hay archivo de bloqueo adicional porque la única dependencia está fijada. Sistema probado: Windows 11.

**Instalación y pruebas.**
```
pip install -r requirements.txt
python -m pytest
```

**Carga inicial y uso** (PowerShell, desde la raíz del repositorio; la base se crea sola en `data/calibrate.db`):
```
$env:PYTHONPATH = "src"
python -m calibrate.cli init                 # carga las unidades de inventory.json
python -m calibrate.cli units
python -m calibrate.cli book --unit MIC-01 --requester "Ana Perez" --start "2026-11-02 10:00" --end "2026-11-02 11:00"
python -m calibrate.cli availability --unit MIC-01 --start "2026-11-02 10:30" --end "2026-11-02 11:30"
python -m calibrate.cli cancel --id 1
python -m calibrate.cli list --all
python -m calibrate.cli reset --yes          # reinicio de datos: borra TODAS las reservas
```
Las fechas deben ser futuras y estar dentro de los 90 días: ajustar los ejemplos a la fecha actual. La tabla completa de comandos está en 1.4.

**Ejemplo de entrada y salida** (salida real, ver `docs/evidence/restart-procedure-output.txt`):
```
$ python -m calibrate.cli book --unit MIC-01 --requester "Ana Perez" --start "2026-11-02 10:00" --end "2026-11-02 11:00"
Reserva creada: #1  MIC-01  2026-11-02 10:00 -> 2026-11-02 11:00  Ana Perez  [ACTIVE]

$ python -m calibrate.cli book --unit MIC-01 --requester "Luis Gomez" --start "2026-11-02 10:30" --end "2026-11-02 11:30"
Error: MIC-01 ya esta reservada en ese horario (reserva 1: 2026-11-02 10:00 a 2026-11-02 11:00).     (código de salida 1)

$ python -m calibrate.cli availability --unit MIC-02 --start "2026-11-02 10:30" --end "2026-11-02 11:30"
MIC-02 LIBRE en ese horario.

$ python -m calibrate.cli cancel --id 2
Reserva cancelada: #2  MIC-02  2026-11-02 10:00 -> 2026-11-02 11:00  Luis Gomez  [CANCELLED]  cancelada: 2026-10-23 20:08:27
```

### 2.3 Dónde están los datos
En `data/calibrate.db` (ignorado por git) o en el archivo indicado por `CALIBRATE_DB`. **`reset --yes` borra todas las reservas, activas y canceladas**; las unidades se conservan y se vuelven a sembrar desde `inventory.json`.

### 2.4 Pruebas
`python -m pytest` ejecuta 65 pruebas (`tests/test_domain.py`, `test_service.py`, `test_persistence.py`), incluidas dos que lanzan procesos separados de la CLI para comprobar la persistencia. No necesitan cuenta ni red.

### 2.5 Evidencia
En `docs/evidence/`: salida de `pytest`, versiones, las corridas en rojo reproducidas desde el historial de git (`red-runs.txt`: 3 errores de colección y 63 pasaron / 2 fallaron), el procedimiento de reinicio (esperado vs. observado) y la re-ejecución manual hecha por la autora (`human-run-melisa.txt`). Ver `docs/evidence/README.md`, que separa lo ejecutado por el agente de lo ejecutado a mano.

### 2.6 Limitaciones
- Un solo laboratorio y una sola zona horaria; sin autenticación.
- Pensado para un usuario por vez en una máquina; la transacción evita reservas dobles entre procesos sobre el mismo archivo, pero no hay servidor ni acceso en red.
- El inventario se edita en `inventory.json`, no desde la CLI; las unidades quitadas del archivo no se borran de la base.
- Un inicio exactamente igual a "ahora" se acepta (solo se rechaza lo anterior).
- Las pruebas de la CLI usan el reloj real (fecha de hoy + 10 días).

**Pendientes**
- Instalación probada en un entorno virtual nuevo con `pip install -r requirements.txt`: no ejecutada todavía (el clon limpio se probó con el pytest ya instalado de la máquina).
- Probado solo en Windows 11 con Python 3.10.11.
- Sin prueba propia para «inicio exactamente igual a ahora».

## 3. Preparación del agente

- **Herramienta**: Claude Code `2.1.283` (salida de `claude --version`, ver `docs/evidence/versions.txt`). Modelo: `claude-sonnet-5-5`, según lo informa el contexto de la sesión (no es salida de un comando).
- **Función del agente**: agente de programación que, bajo revisión humana, redactó la especificación, las pruebas y el código, y ejecutó las pruebas.
- **Motivo de la elección del modelo**: se eligió por tres razones, todas basadas en experiencia previa de la autora y no en una comparación de modelos:
  1. **Conocimiento de Claude Code**: la autora ya conoce cómo trabaja la herramienta (permisos, `CLAUDE.md`, ejecución de comandos), lo que permite delegar y revisar con menos fricción.
  2. **Experiencia previa con este modelo**: lo usó para desarrollar de punta a punta un sistema que ya está desplegado, por lo que conoce sus fortalezas y los puntos que hay que revisar.
  3. **Integración con otras herramientas**: se combina con Claude Chat (para planificar) y con GitHub CLI (para el control de versiones).
- **Configuración externa al repositorio**: la instalación de Claude Code del autor tiene plugins a nivel de usuario (entre ellos `superpowers`, `engineering` y `postman`) que agregan instrucciones y comandos al iniciar la sesión. Al comienzo se invocó el comando `/engineering:system-design` solo para pedir la lectura de `docs/PLAN.md`. Las reglas del proyecto son únicamente las de `CLAUDE.md` y `.claude/settings.json`, que están versionados.
- **`CLAUDE.md`** en la raíz: especificación primero, pruebas antes que código, intervalos semiabiertos, una sola función de choque, sin dependencias nuevas sin preguntar, sin secretos ni datos reales, el agente no hace commits, y actualizar `PROGRESS.md` después de cada tarea.
- **`.claude/settings.json`**: permite sin preguntar `pytest` y git de solo lectura (`status`, `diff`, `log`, `show`, `branch`); pide confirmación para `git commit/push/add`, `rm`/`del` e instalaciones con `pip`.
- **Adaptación específica con evidencia de uso**: la regla de `PROGRESS.md`. Su historial en git muestra una actualización por tarea (hecho / decisiones / siguiente).
- **Contexto entregado al agente**: `docs/PLAN.md`, la especificación del README y las pruebas ya escritas.
- **Contexto excluido**: transcripciones completas de chats, datos reales de estudiantes, credenciales.
- **Aprobaciones realmente concedidas**: las aprobaciones fueron manuales para lo referedo a desarrollo de código e instalaciones, pytest y funciones de git de lectura aprobadas automáticamente, commit/push/pull manual.
- **Qué se revisó antes de aceptar**: se revisó: codigo fuente, tests, salidas en .txt, .gitignore, reglas.

## 4. Decisiones y episodios

- Decisiones y supuestos: tabla en `docs/PLAN.md` sección 1 (lenguaje, SQLite, zona fija, intervalos semiabiertos, límites de 8 h y 90 días, transacción, `reset --yes` que re-siembra sin borrar unidades).
- Cambios de especificación: commits aparte con el motivo en el mensaje (historial recuperable).
- Registro completo de decisiones con su origen (humana o del agente): `docs/decisions.md`.
- Tres episodios de delegación reales (especificación, pruebas primero del choque de intervalos, persistencia/cancelación con un fallo real del agente): `docs/episodes.md`.

<div align="center">
<img width="450" height="450" alt="giphy" src="https://github.com/user-attachments/assets/8f7c4572-fde6-4d23-867d-177865747169" />
</div>
<div align="center">
Gracias
</div>
