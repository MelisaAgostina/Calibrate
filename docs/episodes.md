# Episodios de delegación

Tres episodios reales de esta sesión con Claude Code. Cada uno sigue el formato: objetivo y requisito -> contexto e instrucción -> acción y resultado del agente -> decisión humana y motivo -> enlace.

---

## Episodio 1: redactar la especificación (paso 1)

**Objetivo y requisito.** Escribir la sección 1 del README (especificación) antes de cualquier código, con reglas verificables y criterios de aceptación.

**Contexto e instrucción.** Contexto: `docs/PLAN.md` (decisiones, pruebas requeridas, orden de construcción) y `CLAUDE.md`. Instrucción literal: «lets work on step 1, prior to any code development, lets go through the specs and possible modifications to them».

**Acción y resultado del agente.** Redactó reglas R1-R15, la tabla de comandos, errores, almacenamiento, 10 criterios de aceptación, fuera de alcance y supuestos. Al entregar avisó de cuatro decisiones que el plan no fijaba y que había tomado él:
1. `availability` sin `--unit` lista las unidades libres.
2. `list` muestra solo las activas; `--all` agrega las canceladas.
3. El solicitante se guarda sin espacios en los extremos.
4. `book` valida el intervalo igual que `availability` (R1, R6, R8).

**Decisión humana.** Aceptó esas decisiones («decisions approved») y commiteó la especificación. Motivo: responsabilidad integral sobre el control de versiones del sistema; los requerimientos generados cubren más que los casos de uso mínimos.

**Enlace.** Commit `62e4191` («Spec inicial»); `README.md` sección 1.

---

## Episodio 2: pruebas primero para el choque de intervalos (pasos 2 y 3)

**Objetivo y requisito.** Pruebas en rojo antes del código, cubriendo los límites de la regla de choque (R3/R4) y los de duración y anticipación (R8/R9).

**Contexto e instrucción.** Contexto: la especificación ya commiteada y la lista de pruebas de `docs/PLAN.md` sección 3. Instrucciones literales: «ok lets do step 2, same way we've been working so far, don't apply anything until i revised it» y, tras revisar, «decisions approved, step 2 commited»; con eso el agente siguió con el paso 3 (`domain.py`).

**Acción y resultado del agente.**
- Escribió `tests/test_domain.py`, `test_service.py` y `test_persistence.py` (más `requirements.txt`, `pytest.ini`, `inventory.json`). Las pruebas definen la API que el código debe tener (`overlaps`, `validate_interval`, `CalibrateService(...)`).
- Instaló pytest y ejecutó la suite: **3 errores de colección** (`No module named 'calibrate'`), el rojo esperado.
- Avisó de lo que las pruebas no resolvían: el inicio exactamente igual a «ahora» no está probado (la especificación no lo dice), la variable `CALIBRATE_DB` no estaba en la especificación, y las pruebas de la CLI usan el reloj real.
- Después escribió `domain.py`: `tests/test_domain.py` pasó (25 pruebas).

**Decisión humana.** Aprobó las decisiones señaladas y commiteó las pruebas en rojo antes del código. Revisó las pruebas de límites (README sección 3: «se revisó: código fuente, tests…»). Motivo: verificar que el sistema cumpla con las funciones minimas y las consignas del challenge; los archivos quedaron sin commitear hasta que los revisé.

**Enlace.** Commit `303f661` (pruebas rojas), commit `1420714` (`test_domain.py` en verde); `tests/test_domain.py`, `docs/evidence/pytest-output.txt`.

---

## Episodio 3: persistencia, cancelación y una afirmación del agente sin verificar (pasos 4-6)

**Objetivo y requisito.** Repositorio SQLite y servicio que cumplan cancelar sin borrar (R12), persistencia entre procesos y la regla de transacción (R15); luego CLI y evidencia real.

**Contexto e instrucción.** Contexto: las pruebas en rojo y la especificación. Instrucciones literales: «same way we worked on step 3, now lets do 4», lo mismo para los pasos 5 y 6.

**Acción y resultado del agente.**
- Paso 4: `repository.py` y `service.py`. Suite: **63 pasaron y 2 fallaron** (las dos pruebas de la CLI, porque `calibrate.cli` aún no existía). Eligió comprobar el choque en Python con la misma `overlaps` (no en SQL) para mantener una sola función.
- Paso 5: `cli.py`; suite completa **65 pasaron**; sesión de demostración manual.
- Paso 6: guardó en `docs/evidence/` la salida de `pytest`, las versiones y un procedimiento de 13 pasos con un proceso por comando (esperado vs. observado, 13/13). Aclaró que eso lo ejecutó el agente y que la autora aún debía repetirlo.

**Decisión humana.** Aceptó el código tras revisarlo y repetir los comandos a mano (65 pruebas pasaron; el procedimiento coincidió, incluido `reset --yes`); rechazó la explicación sin pruebas del agente. Motivo: la evidencia debe distinguir lo observado de lo supuesto.

**Enlace.** Commits `21bd153` (repositorio y servicio), `6bd0e76` (CLI), `7b406c6` y `4067a86` (evidencia); `docs/evidence/README.md`.
