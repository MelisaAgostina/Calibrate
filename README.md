# Calibrate

Sistema de reservas de equipos de laboratorio por consola (Python 3 + SQLite).

## 1. Especificación

### 1.1 Objetivo
Reservar unidades de equipos de laboratorio por franjas horarias, sin superposiciones, y poder consultar disponibilidad y cancelar. Interfaz de consola; los datos persisten entre ejecuciones.

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
SQLite en `data/calibrate.db` (ignorado por git). Tablas: `units(id, name)` y `reservations(id, unit_id, requester, start, end, status, created_at, cancelled_at)`; `status` restringido a `ACTIVE` / `CANCELLED`.

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

## 2. Solución

_(pendiente)_

## 3. Preparación del agente

_(pendiente)_

## 4. Decisiones y episodios

_(pendiente)_


<div style="align-items: center">
Gracias
<img width="450" height="450" alt="giphy" src="https://github.com/user-attachments/assets/8f7c4572-fde6-4d23-867d-177865747169" />
</div>
