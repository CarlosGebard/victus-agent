from victus_platform.identity.local_session import get_valid_access_token
from tools.contracts import ToolIdentity


async def resolve_identity() -> ToolIdentity:
    token = await get_valid_access_token()
    return ToolIdentity(authenticated=bool(token))
