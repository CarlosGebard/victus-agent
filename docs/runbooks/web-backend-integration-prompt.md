# Prompt Para Integrar El Web Backend Con victus-agent MCP

Usa este prompt en el repositorio del backend web para implementar el contrato mínimo que necesita
`victus-agent`.

````markdown
# Integración Victus Web Backend <-> victus-agent MCP

Necesitamos integrar el backend web con el MCP server local `victus-agent` usando un patrón de token
relay.

## Arquitectura esperada

- El usuario inicia sesión localmente desde el CLI de `victus-agent`.
- Comando local:

```bash
victus login
```

- Ese comando guarda el JWT en:

```text
~/.victus/session.json
```

- El MCP server local lee el token en cada llamada.
- El MCP server llama al backend web con:
  - endpoint: `GET /v1/me`
  - header: `Authorization: Bearer <jwt>`
- El backend web valida el JWT y responde con el perfil autenticado del usuario.

## Contrato requerido del backend

Implementar o confirmar este endpoint:

```http
GET /v1/me
Authorization: Bearer <jwt>
```

## Respuesta 200

Debe devolver JSON estable, por ejemplo:

```json
{
  "id": "user_123",
  "email": "user@example.com",
  "name": "Carlos",
  "display_name": "Carlos",
  "plan": "free",
  "profile": {
    "goals": ["nutrition_tracking"],
    "restrictions": ["lactose_intolerance"],
    "preferences": ["high_protein"]
  }
}
```

Campos mínimos recomendados:

- `id`
- `email`
- `name` o `display_name`
- `profile`

## Respuesta 401

Cuando el JWT falta, expiró o es inválido:

```json
{
  "error": "unauthorized",
  "message": "Invalid or expired token"
}
```

## Respuesta 5xx

Formato recomendado:

```json
{
  "error": "server_error",
  "message": "Unable to load profile"
}
```

## Variables de entorno

El MCP client usará:

```bash
BACKEND_API_URL=http://localhost:8000/v1
```

En producción:

```bash
BACKEND_API_URL=https://api.tu-servidor-web.com/v1
```

## Tests esperados en backend

Agregar tests para:

1. `GET /v1/me` sin token retorna `401`.
2. `GET /v1/me` con token inválido retorna `401`.
3. `GET /v1/me` con token válido retorna `200` y perfil JSON.
4. El endpoint no expone secretos ni claims internos sensibles.
5. El endpoint usa el `sub` o user id del JWT para cargar el perfil correcto.

## Criterio de aceptación

Desde `victus-agent` debe funcionar:

```bash
victus login
BACKEND_API_URL=http://localhost:8000/v1 victus mcp-call recuperar_perfil '{}'
```

La respuesta debe incluir un resumen legible del perfil autenticado.
````
