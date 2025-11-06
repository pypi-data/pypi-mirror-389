

import httpx
import asyncio
import hashlib
import inspect
from urllib.parse import urlencode
from fastapi import Security
from fastapi.params import Depends
from fastapi.security import SecurityScopes

from tendril.connectors.keycloak.client import KeycloakClient
from tendril.connectors.keycloak.client import make_scheme
from tendril.connectors.keycloak.client import build_get_user
from tendril.connectors.keycloak.client import KeycloakUserModel

from tendril.connectors.keycloak.admin import KeycloakAdminClient
from tendril.authn.scaffold import null_dependency

from tendril.config import AUTH_USERINFO_CACHING
from tendril.config import KEYCLOAK_SERVER_URL
from tendril.config import KEYCLOAK_REALM
from tendril.config import KEYCLOAK_AUDIENCE
from tendril.config import KEYCLOAK_CLIENT_ID
from tendril.config import KEYCLOAK_CLIENT_SECRET
from tendril.config import KEYCLOAK_CALLBACK_URL
from tendril.config import KEYCLOAK_ADMIN_CLIENT_ID
from tendril.config import KEYCLOAK_ADMIN_CLIENT_SECRET
from tendril.config import KEYCLOAK_NAMESPACE
from tendril.config import KEYCLOAK_SSL_VERIFICATION

from tendril.apiserver.server import fastapi_app

from tendril.utils import log
logger = log.get_logger(__name__, log.DEBUG)

logger.info(f"Using Keycloak parameters:\n"
            f"  - url           {KEYCLOAK_SERVER_URL} \n"
            f"  - realm         {KEYCLOAK_REALM} \n"
            f"  - client_id     {KEYCLOAK_CLIENT_ID} \n"
            # f"  - client_secret {KEYCLOAK_CLIENT_SECRET} \n"
            # f"  - admin_secret  {KEYCLOAK_ADMIN_CLIENT_SECRET} \n"
            f"  - callback_uri  {KEYCLOAK_CALLBACK_URL} \n")

if AUTH_USERINFO_CACHING == 'platform':
    logger.info("Using platform level caching for Keycloak UserInfo")
    from tendril.caching import platform_cache as cache
else:
    logger.info("Not caching Keycloak UserInfo")
    from tendril.caching import no_cache as cache


idp = KeycloakClient(
    server_url=KEYCLOAK_SERVER_URL,
    realm=KEYCLOAK_REALM,
    audience=KEYCLOAK_AUDIENCE,
    client_id=KEYCLOAK_CLIENT_ID,
    client_secret=KEYCLOAK_CLIENT_SECRET,
    ssl_verify=KEYCLOAK_SSL_VERIFICATION,
)

_scheme = make_scheme(KEYCLOAK_SERVER_URL, KEYCLOAK_REALM)
get_user = build_get_user(idp, _scheme)
fastapi_app.swagger_ui_init_oauth = {
    "clientId": KEYCLOAK_CLIENT_ID,
    "usePkceWithAuthorizationCodeGrant": True,
    "clientSecret": KEYCLOAK_CLIENT_SECRET,
}

admin = KeycloakAdminClient(
    server_url=KEYCLOAK_SERVER_URL,
    realm=KEYCLOAK_REALM,
    admin_client_id=KEYCLOAK_ADMIN_CLIENT_ID,
    admin_client_secret=KEYCLOAK_ADMIN_CLIENT_SECRET,
    ssl_verify=KEYCLOAK_SSL_VERIFICATION,
)

swagger_auth = null_dependency
AuthUserModel = KeycloakUserModel


def security(scopes=None):
    kwargs = {}
    if scopes:
        kwargs['scopes'] = scopes
    return Security(get_user, **kwargs)


def _key_func(user_id):
    return user_id

@cache(namespace="userinfo", ttl=86400, key=lambda user_id: user_id)
async def get_user_profile(user_id: str):
    # Detect service accounts
    if user_id.startswith("service-account-"):
        client_id = user_id.replace("service-account-", "")
        try:
            return await admin.get_service_account_user(client_id)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Service account not found: {user_id}")
            raise

    # Regular human user
    try:
        return await admin.get_user(user_id)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        raise


def is_service_account(profile: dict) -> bool:
    """
    Detects whether this Keycloak user profile represents
    a service account automatically created for a client.
    """
    return profile.get("username", "").startswith("service-account-")


@cache(namespace="userstub", ttl=86400, key=_key_func)
async def get_user_stub(user_id):
    """
    Retrieve a simplified user stub profile from Keycloak.

    Adds `nickname` and `picture` fields if missing,
    and detects service (M2M) accounts based on username.
    """
    profile = await get_user_profile(user_id)

    if is_service_account(profile):
        profile["description"] = f"Service account for {profile.get('username')}"
        return profile

    name = profile.get("firstName", "") + " " + profile.get("lastName", "")
    name = name.strip() or profile.get("username", user_id)

    email = profile.get("email")
    nickname = profile.get("username") or (email.split("@")[0] if email else name)
    user_id_field = profile.get("id") or user_id

    if email:
        email_hash = hashlib.md5(email.lower().encode("utf-8")).hexdigest()
        gravatar_url = f"https://www.gravatar.com/avatar/{email_hash}?{urlencode({'d': 'identicon', 's': '128'})}"
    else:
        gravatar_url = None

    return {
        "name": name,
        "nickname": nickname,
        "picture": gravatar_url,
        "user_id": user_id_field,
    }


def init():
    pass
