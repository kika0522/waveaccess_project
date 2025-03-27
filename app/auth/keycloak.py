from fastapi import Depends, HTTPException, Security
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.config import settings
import requests

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class KeycloakAuth:
    def __init__(self):
        self.issuer = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}"
        self.public_key = self._get_public_key()

    def _get_public_key(self):
        jwks_url = f"{self.issuer}/protocol/openid-connect/certs"
        response = requests.get(jwks_url)
        keys = response.json().get("keys", [])
        if not keys:
            raise RuntimeError("Не удалось получить публичный ключ Keycloak")
        return f"-----BEGIN PUBLIC KEY-----\n{keys[0]['x5c'][0]}\n-----END PUBLIC KEY-----"

    def decode_token(self, token: str):
        try:
            payload = jwt.decode(token, self.public_key, algorithms=["RS256"], audience=settings.KEYCLOAK_CLIENT_ID)
            return payload
        except JWTError:
            raise HTTPException(status_code=401, detail="Недействительный токен")

    async def get_current_user(self, token: str = Security(oauth2_scheme)):
        user = self.decode_token(token)
        return user

keycloak = KeycloakAuth()
