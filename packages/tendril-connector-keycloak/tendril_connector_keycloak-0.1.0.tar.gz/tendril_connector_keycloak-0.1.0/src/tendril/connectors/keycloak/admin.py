
import time
import httpx
import asyncio
from .base import KeycloakClientBase


class KeycloakAdminClient(KeycloakClientBase):
    def __init__(self, server_url: str, realm: str,
                 admin_client_id: str, admin_client_secret: str,
                 ssl_verify: bool = True, timeout: int = 10):
        super().__init__(server_url, realm, ssl_verify)
        self.admin_client_id: str = admin_client_id
        self.admin_client_secret: str = admin_client_secret

        self._token = None
        self._token_expiry = 0
        self._client = httpx.AsyncClient(verify=ssl_verify, timeout=timeout)

    @property
    def _token_url(self):
        return self._protocol_url + "/token"

    @property
    def _realm_admin_url(self):
        return f"{self._server_url}/admin/realms/{self.realm}"

    async def _get_token(self):
        if self._token and time.time() < self._token_expiry - 30:
            return self._token

        data = {
            "grant_type": "client_credentials",
            "client_id": self.admin_client_id,
            "client_secret": self.admin_client_secret,
        }

        response = await self._client.post(self._token_url, data=data)
        response.raise_for_status()
        payload = response.json()

        self._token = payload["access_token"]
        self._token_expiry = time.time() + payload.get("expires_in", 60)
        return self._token

    async def _headers(self) -> dict[str, str]:
        token = await self._get_token()
        return {
            "Authorization": f"Bearer {self._token}",
        }

    async def _get(self, path: str, retry: bool = True) -> dict:
        headers = await self._headers()
        url = f"{self._realm_admin_url}/{path.lstrip('/')}"
        response = await self._client.get(url, headers=headers)
        if response.status_code == 401 and retry:
            # Token expired or invalid → refresh and retry once
            self._token = None
            return await self._get(path, retry=False)
        response.raise_for_status()
        return response.json()

    async def get_user(self, user_id: str) -> dict:
        return await self._get(f"/users/{user_id}")

    async def get_client(self, client_id: str) -> dict:
        clients = await self._get(f"clients?clientId={client_id}")
        if not clients:
            raise ValueError(f'Client {client_id} not found')
        return clients[0]

    async def get_service_account_user(self, client_id: str) -> dict:
        client = await self.get_client(client_id)
        client_uuid = client["id"]
        return await self._get(f"clients/{client_uuid}/service-account-user")

    async def close(self):
        await self._client.aclose()
