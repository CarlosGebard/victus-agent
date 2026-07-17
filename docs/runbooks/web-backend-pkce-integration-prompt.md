# Prompt Para Integrar OAuth PKCE Entre Web Backend y victus-agent

Usa este prompt en el repositorio del backend web. Reemplaza el flujo de token manual por un flujo
profesional de OAuth Authorization Code + PKCE para CLI/MCP.

````markdown
# Integración OAuth PKCE Para victus-agent MCP

Necesitamos integrar el backend web con `victus-agent` usando OAuth Authorization Code + PKCE.

## Objetivo

Permitir que el usuario ejecute:

```bash
victus login
```

Y que el CLI:

1. Abra el navegador.
2. Envíe al usuario al backend web para iniciar sesión y autorizar.
3. Reciba un `authorization_code` en un callback local.
4. Intercambie `code + code_verifier` por tokens.
5. Guarde la sesión localmente en `~/.victus/session.json`.
6. Permita que el MCP server use el access token para llamar `GET /v1/me`.

## Flujo Requerido

```text
victus login
  -> genera code_verifier, code_challenge S256 y state
  -> levanta callback local en http://127.0.0.1:{random_port}/callback
  -> abre navegador con GET /oauth/authorize
  -> usuario inicia sesión y aprueba
  -> backend redirige a http://127.0.0.1:{random_port}/callback?code=...&state=...
  -> CLI valida state
  -> CLI llama POST /oauth/token con code_verifier
  -> backend responde access_token, refresh_token, expires_in, token_type
  -> CLI guarda sesión local
```

## Endpoints Backend Necesarios

```http
GET /oauth/authorize
POST /oauth/token
GET /v1/me
POST /oauth/revoke
```

`POST /oauth/revoke` puede ser fase 2, pero es recomendado para `victus logout`.

## Cliente OAuth

Registrar un cliente público para CLI:

```text
client_id: victus-cli
client_type: public
client_secret: none
grant_types:
  - authorization_code
  - refresh_token
redirect_uri_policy:
  - allow loopback redirects on 127.0.0.1 with dynamic ports
required_pkce: true
allowed_code_challenge_methods:
  - S256
scopes:
  - openid
  - profile
  - email
  - offline_access
```

El backend debe permitir redirect URIs con puerto dinámico:

```text
http://127.0.0.1:{port}/callback
```

No exigir client secret para `victus-cli`; es un cliente público.

## GET /oauth/authorize

Debe aceptar:

```text
response_type=code
client_id=victus-cli
redirect_uri=http://127.0.0.1:{port}/callback
scope=openid profile email offline_access
state={random_state}
code_challenge={base64url_sha256_code_verifier}
code_challenge_method=S256
```

Requisitos:

- El usuario debe autenticarse en el navegador si no tiene sesión.
- El usuario debe ver o aceptar que está autorizando `victus-cli`.
- El backend debe guardar temporalmente el `code_challenge` asociado al authorization code.
- El authorization code debe expirar rápido, recomendado 5-10 minutos.
- El authorization code debe ser de un solo uso.
- El redirect debe devolver `code` y el mismo `state`.

Ejemplo de redirect:

```http
302 Location: http://127.0.0.1:49152/callback?code=AUTH_CODE&state=STATE
```

## POST /oauth/token Para Authorization Code

Request:

```http
POST /oauth/token
Content-Type: application/json
```

```json
{
  "grant_type": "authorization_code",
  "client_id": "victus-cli",
  "code": "AUTH_CODE",
  "redirect_uri": "http://127.0.0.1:49152/callback",
  "code_verifier": "ORIGINAL_CODE_VERIFIER"
}
```

Validaciones:

- `code` existe, no expiró y no fue usado.
- `client_id` coincide.
- `redirect_uri` coincide exactamente con el usado en `/oauth/authorize`.
- `code_verifier` produce el `code_challenge` guardado.
- `code_challenge_method` debe ser `S256`.

Response 200:

```json
{
  "access_token": "ACCESS_TOKEN",
  "refresh_token": "REFRESH_TOKEN",
  "expires_in": 3600,
  "token_type": "Bearer",
  "scope": "openid profile email offline_access"
}
```

## POST /oauth/token Para Refresh Token

Request:

```json
{
  "grant_type": "refresh_token",
  "client_id": "victus-cli",
  "refresh_token": "REFRESH_TOKEN"
}
```

Response 200:

```json
{
  "access_token": "NEW_ACCESS_TOKEN",
  "refresh_token": "ROTATED_REFRESH_TOKEN",
  "expires_in": 3600,
  "token_type": "Bearer",
  "scope": "openid profile email offline_access"
}
```

Recomendado:

- Rotar refresh tokens.
- Revocar refresh token anterior al emitir uno nuevo.
- Detectar reuse de refresh token antiguo y revocar la sesión.

## GET /v1/me

Request:

```http
GET /v1/me
Authorization: Bearer ACCESS_TOKEN
```

Response 200:

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

Response 401:

```json
{
  "error": "unauthorized",
  "message": "Invalid or expired token"
}
```

## POST /oauth/revoke

Fase recomendada para `victus logout`.

Request:

```json
{
  "client_id": "victus-cli",
  "token": "REFRESH_TOKEN",
  "token_type_hint": "refresh_token"
}
```

Response:

```http
200 OK
```

## Archivo Local Esperado En victus-agent

Después del login, `victus-agent` guardará:

```json
{
  "access_token": "ACCESS_TOKEN",
  "refresh_token": "REFRESH_TOKEN",
  "expires_at": "2026-07-16T20:30:00Z",
  "token_type": "Bearer",
  "scope": "openid profile email offline_access"
}
```

Ruta:

```text
~/.victus/session.json
```

Permisos esperados:

```text
~/.victus             0700
~/.victus/session.json 0600
```

## Tests Backend Requeridos

1. `/oauth/authorize` rechaza requests sin `code_challenge`.
2. `/oauth/authorize` rechaza `code_challenge_method` distinto de `S256`.
3. `/oauth/authorize` acepta redirect loopback `127.0.0.1` con puerto dinámico.
4. `/oauth/token` rechaza `code_verifier` incorrecto.
5. `/oauth/token` rechaza reuse del mismo authorization code.
6. `/oauth/token` emite `access_token` y `refresh_token` con `offline_access`.
7. `/oauth/token` refresca access token con refresh token válido.
8. `/oauth/token` rota refresh tokens si el backend soporta rotación.
9. `/v1/me` retorna 401 sin token.
10. `/v1/me` retorna 401 con token inválido o expirado.
11. `/v1/me` retorna perfil correcto con access token válido.
12. `/oauth/revoke` revoca refresh token y evita futuros refresh.

## Tests De Integración Esperados

Con backend local levantado:

```bash
victus login
BACKEND_API_URL=http://localhost:8000/v1 victus mcp-call recuperar_perfil '{}'
```

Resultado esperado:

```json
{
  "status": "success",
  "data": {
    "summary": "...",
    "profile": {
      "id": "user_123"
    }
  }
}
```

## Notas Si Se Usa Better Auth

Si el backend está en TypeScript/Next.js/Hono u otro stack compatible con Better Auth, evaluar:

- OAuth 2.1 Provider plugin para Authorization Code + PKCE.
- Device Authorization plugin como alternativa para CLI sin callback local o entornos remotos.
- Bearer/JWT support para validar `Authorization: Bearer` en `/v1/me`.

Preferencia para desktop local:

```text
Authorization Code + PKCE + loopback redirect
```

Fallback útil:

```text
Device Authorization Grant
```

especialmente si el CLI corre en servidor remoto, contenedor, SSH, o ambiente donde abrir/capturar
browser local sea incómodo.
````

