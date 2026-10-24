# Decisiones

Registro de decisiones con su origen. Las del plan inicial están en `docs/PLAN.md` sección 1; aquí van las tomadas o ajustadas durante la construcción.

| Decisión | Origen | Motivo | Dónde queda |
|---|---|---|---|
| `reset --yes` borra todas las reservas (activas y canceladas) y vuelve a sembrar las unidades faltantes; nunca borra unidades | Humana (propuesta del agente, la autora pidió «reseed»); luego registrada en el plan | La base queda usable justo después de `reset`; reutiliza el sembrado de `init` | `docs/PLAN.md` §1, README 1.4 |
| Se agregan al plan pruebas de límites (8 h, 90 días), cancelar dos veces, rebook de franja cancelada, `init` repetido, `reset` con y sin `--yes` | Agente propuso, humana aprobó | Cubren aristas que la lista original no probaba | `docs/PLAN.md` §3 |
| Transacción `BEGIN IMMEDIATE` para comprobar y reservar | Agente propuso, humana aprobó | Evita que dos procesos reserven la misma franja | README R15, `repository.py` |
| Se eliminó del plan la sección «Early actions» | Humana | Los commits los hace ella; el orden ya estaba en la sección 5 | `docs/PLAN.md` |
| `availability` sin `--unit` lista unidades libres; con `--unit`, indica las reservas que la bloquean | Agente decidió, humana aprobó | El plan no lo fijaba | README 1.4 |
| `list` muestra activas; `--all` agrega canceladas | Agente decidió, humana aprobó | El plan no lo fijaba | README 1.4 |
| El solicitante se guarda sin espacios en los extremos | Agente decidió, humana aprobó | Evita duplicados visuales; `"   "` sigue siendo inválido | README R11 |
| Un solo tipo de error de usuario (`ValidationError`) para todo | Agente decidió (definido por las pruebas), humana aprobó | La CLI solo necesita un mensaje y un código de salida | `domain.py`, `cli.py` |
| El choque se calcula en Python con `domain.overlaps`, no en SQL | Agente decidió | Una sola función de choque, como pide el plan | `service.py` |
| El esquema se crea en cada conexión (`CREATE TABLE IF NOT EXISTS`) | Agente decidió | `list` y los servicios funcionan aunque no se haya corrido `init` | `repository.py` |
| `CALIBRATE_DB` selecciona el archivo de base de datos | Agente propuso (lo necesitan las pruebas de la CLI), humana aprobó | Probar sin tocar `data/calibrate.db` | README 1.6 |
| Inicio exactamente igual a «ahora» se acepta | Agente decidió; humana aprobó | La especificación solo rechaza lo anterior a ahora; sin prueba propia | README 2.6 |
| Las pruebas de la CLI usan el reloj real (hoy + 10 días) | Agente decidió, señalado como limitación | La CLI no tiene reloj inyectable | README 2.6 |
