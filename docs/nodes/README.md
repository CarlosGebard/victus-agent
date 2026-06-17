# Victus Nodes Map

Los contratos de nodos se agrupan por responsabilidad. La distincion principal es si el nodo
puede conducir a herramientas/acciones de dominio o si solo prepara, enruta o cierra el turno.

## `runtime/`

Nodos de orquestacion. No ofrecen herramientas de dominio al modelo.

- [`context_bootstrap`](runtime/context-bootstrap-node.md): carga contexto compacto y pendiente.
- [`safety_precheck`](runtime/safety-precheck-node.md): evalua riesgo antes de la ejecucion normal.
- [`route_intent`](runtime/intent-router-node.md): decide el branch semantico objetivo.
- [`summary_after_response`](runtime/summary-after-response-node.md): resume el turno despues de responder.

Nodos runtime implementados sin contrato dedicado todavia:

- `normalize_request`: normaliza `request.raw_text`/`request.original_text` a `request.working_text`.
- `compose_response`: compone la respuesta final, con LLM si hay cliente configurado.

## `tool-nodes/`

Nodos o branches que representan capacidades que eventualmente ofrecen herramientas, acciones o
acceso a servicios de dominio al modelo. Deben pasar por safety, routing y tool gates antes de
mutar estado o consultar evidencia.

- [`event_capture`](tool-nodes/event-capture-node.md): captura eventos de usuario como comidas,
  biometria o sintomas.
- [`profile_update`](tool-nodes/profile-update-node.md): actualiza preferencias, restricciones y
  datos persistentes de perfil.
- [`plan_intent`](tool-nodes/plan-intent-node.md): gestiona objetivos, planes, revisiones y
  artefactos de planificacion.
- [`evidence_answer`](tool-nodes/evidence-answer-node.md): usa evidencia/RAG para responder o
  respaldar recomendaciones.

## `interaction/`

Nodos conversacionales auxiliares. No ejecutan herramientas de dominio por si mismos.

- [`clarification`](interaction/clarification-node.md): pide informacion minima para desbloquear
  una accion o ruta.

## Nodos Faltantes

- `semantic_canonicalizer`: convertiria mensajes cortos o ambiguos en una consulta autonoma.
- `projection_load`: cargaria proyecciones minimas antes de un branch/tool.
- `tool_dispatch`: elegiria y ejecutaria el handler permitido para el route seleccionado.
- `projector_update`: correria projectors afectados por eventos emitidos.
- `mixed_intent_resolver`: separaria o secuenciaria solicitudes con multiples intenciones.
