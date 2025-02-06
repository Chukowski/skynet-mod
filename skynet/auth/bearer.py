from fastapi import Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from skynet.auth.jwt import authorize
from skynet.env import app_uuid, bypass_auth


class JWTBearer(HTTPBearer):
    def __init__(self):
        super().__init__(auto_error=not bypass_auth)

    async def __call__(self, request: Request):
        if bypass_auth or request.headers.get('X-Skynet-UUID') == app_uuid:
            request.state.decoded_jwt = {}
            return None

        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        request.state.decoded_jwt = await authorize(credentials.credentials)
        return credentials.credentials
