# Victus Nodes Map

## Nodos Implementados

### 1. `normalize_request`

Qué hace: toma `request.original_text` o compat `request.raw_text`, lo normaliza y escribe una sola vista activa: `request.working_text`.

Dónde está:
- Nodo: `src/agent/nodes/runtime.py`
- Conectado en grafo: `src/agent/graph.py`

### 2. `context_bootstrap`

Qué hace: carga `ConversationStateSummary` y `PendingInteractionState` si hay `conversation_id`, y actualiza `request.working_text` si necesita contexto pendiente o traducción.

Dónde está:
- Nodo: `src/agent/nodes/context.py`
- Contrato: `docs/nodes/context-bootstrap-node.md`
- Conectado en grafo: `src/agent/graph.py`

### 3. `safety_precheck`

Qué hace: revisa el texto de seguridad en inglés con reglas declarativas y escribe `safety.decision`, `safety.severity`, `safety.matched_rules` y `safety.reason_codes`.

Dónde está:
- Nodo: `src/agent/nodes/runtime.py`
- Contrato: `docs/nodes/safety-precheck-node.md`
- Conectado en grafo: `src/agent/graph.py`

### 4. `route_intent`

Qué hace: enruta `request.working_text` hacia un graph/route semántico y escribe `intent`.

Dónde está:
- Nodo: `src/agent/nodes/runtime.py`
- Router: `src/application/routing/`
- Contrato: `docs/nodes/intent-router-node.md`
- Conectado en grafo: `src/agent/graph.py`

### 5. `compose_response`

Qué hace: genera la respuesta final; si hay `LLMClient`, usa el puerto LLM, si no responde de forma determinística.

Dónde está:
- Nodo: `src/agent/nodes/runtime.py`
- Puerto LLM: `src/application/ports/llm.py`
- Conectado en grafo: `src/agent/graph.py`

### 6. `summarize_after_response`

Qué hace: actualiza `ConversationStateSummary` después de la respuesta y persiste/limpia `PendingInteractionState`.

Dónde está:
- Nodo: `src/agent/nodes/summary.py`
- Contrato: `docs/nodes/summary-after-response-node.md`
- Conectado en grafo: `src/agent/graph.py`

## Nodos Faltantes

### 1. `semantic_canonicalizer`

Qué haría: convertiría mensajes cortos o ambiguos en una consulta autónoma para routing usando contexto bootstrap.

Dónde debería vivir:
- Nodo: `src/agent/nodes/context.py` o `src/agent/nodes/canonicalizer.py`
- Servicio: `src/application/routing/`

### 2. `projection_load`

Qué haría: cargaría proyecciones mínimas del usuario antes de ejecutar un branch o tool.

Dónde debería vivir:
- Nodo: `src/agent/nodes/projections.py`
- Repositorio: `src/infrastructure/repositories/projections.py`

### 3. `tool_dispatch`

Qué haría: elegiría y ejecutaría el handler permitido para el route seleccionado.

Dónde debería vivir:
- Nodo: `src/agent/nodes/tools.py`
- Contratos: `src/domain/tools/`

### 4. `event_capture`

Qué haría: ejecutaría capturas como `meal.logged`, `biometrics.logged` o `symptom.logged`.

Dónde debería vivir:
- Nodo/branch: `src/agent/nodes/event_capture.py`
- Contrato: `docs/nodes/event-capture-node.md`

### 5. `projector_update`

Qué haría: correría projectors afectados por eventos emitidos y actualizaría proyecciones.

Dónde debería vivir:
- Nodo: `src/agent/nodes/projectors.py`
- Servicio: `src/application/projections/runner.py`

### 6. `profile_update`

Qué haría: actualizaría restricciones, preferencias y contexto durable del usuario.

Dónde debería vivir:
- Nodo/branch: `src/agent/nodes/profile_update.py`
- Contrato: `docs/nodes/profile-update-node.md`

### 7. `plan_intent`

Qué haría: manejaría creación/revisión de objetivos, sesiones, revisiones y artifacts de planificación.

Dónde debería vivir:
- Nodo/branch: `src/agent/nodes/plan_intent.py`
- Contrato: `docs/nodes/plan-intent-node.md`

### 8. `evidence_answer`

Qué haría: respondería preguntas de evidencia sin mutar estado de usuario por defecto.

Dónde debería vivir:
- Nodo/branch: `src/agent/nodes/evidence_answer.py`
- Contrato: `docs/nodes/evidence-answer-node.md`

### 9. `clarification`

Qué haría: pediría la mínima información necesaria y dejaría estado resumible.

Dónde debería vivir:
- Nodo/branch: `src/agent/nodes/clarification.py`
- Contrato: `docs/nodes/clarification-node.md`

### 10. `mixed_intent_resolver`

Qué haría: separaría o secuenciaría solicitudes con múltiples intenciones.

Dónde debería vivir:
- Nodo/branch: `src/agent/nodes/mixed_intent.py`
