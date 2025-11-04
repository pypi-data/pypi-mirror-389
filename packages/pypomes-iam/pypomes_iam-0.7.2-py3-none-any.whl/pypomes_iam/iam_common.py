import requests
import sys
from datetime import datetime
from enum import StrEnum, auto
from logging import Logger
from pypomes_core import TZ_LOCAL, exc_format
from pypomes_crypto import crypto_jwk_convert
from threading import RLock
from typing import Any, Final


class IamServer(StrEnum):
    """
    Supported IAM servers.
    """
    JUSBR = auto()
    KEYCLOAK = auto()


class IamParam(StrEnum):
    """
    Parameters for configuring *IAM* servers.
    """
    ADMIN_ID = "admin-id"
    ADMIN_SECRET = "admin-secret"
    CLIENT_ID = "client-id"
    CLIENT_REALM = "client-realm"
    CLIENT_SECRET = "client-secret"
    ENDPOINT_CALLBACK = "endpoint-callback"
    ENDPOINT_LOGIN = "endpoint-login"
    ENDPOINT_LOGOUT = "endpoint_logout"
    ENDPOINT_TOKEN = "endpoint-token"
    ENDPOINT_EXCHANGE = "endpoint-exchange"
    LOGIN_TIMEOUT = "login-timeout"
    PK_EXPIRATION = "pk-expiration"
    PK_LIFETIME = "pk-lifetime"
    PUBLIC_KEY = "public-key"
    RECIPIENT_ATTR = "recipient-attr"
    URL_BASE = "url-base"
    USERS = "users"


class UserParam(StrEnum):
    """
    Parameters for handling *IAM* users.
    """
    ACCESS_TOKEN = "access-token"
    REFRESH_TOKEN = "refresh-token"
    ACCESS_EXPIRATION = "access-expiration"
    REFRESH_EXPIRATION = "refresh-expiration"
    # transient attributes
    LOGIN_EXPIRATION = "login-expiration"
    LOGIN_ID = "login-id"
    REDIRECT_URI = "redirect-uri"


# The configuration parameters for the IAM servers are specified dynamically dynamically with *iam_setup()*
# Specifying configuration parameters with environment variables can be done in two ways:
#
# 1. for a single *IAM* server, specify the data set
#       - *<APP_PREFIX>_IAM_ADMIN_ID*             (optional, needed if administrative duties are performed)
#       - *<APP_PREFIX>_IAM_ADMIN_PWD*            (optional, needed if administrative duties are performed)
#       - *<APP_PREFIX>_IAM_CLIENT_ID*            (required)
#       - *<APP_PREFIX>_IAM_CLIENT_REALM*         (required)
#       - *<APP_PREFIX>_IAM_CLIENT_SECRET*        (required)
#       - *<APP_PREFIX>_IAM_ENDPOINT_CALLBACK*    (required)
#       - *<APP_PREFIX>_IAM_ENDPOINT_EXCHANGE*    (required)
#       - *<APP_PREFIX>_IAM_ENDPOINT_LOGIN*       (required)
#       - *<APP_PREFIX>_IAM_ENDPOINT_LOGOUT*      (required)
#       - *<APP_PREFIX>_IAM_ENDPOINT_PROVIDER*    (optional, needed if requesting tokens to providers)
#       - *<APP_PREFIX>_IAM_ENDPOINT_TOKEN*       (required)
#       - *<APP_PREFIX>_IAM_LOGIN_TIMEOUT*        (optional, defaults to no timeout)
#       - *<APP_PREFIX>_IAM_PK_LIFETIME*          (optional, defaults to non-terminating lifetime)
#       - *<APP_PREFIX>_IAM_RECIPIENT_ATTR*       (required)
#       - *<APP_PREFIX>_IAM_URL_BASE*             (required)
#
# 2. for multiple *IAM* servers, specify the data set above for each server,
#    respectively replacing *IAM* with a name in *IamServer* (currently, *JUSBR* and *KEYCLOAK* are supported).
#
# 3. the parameters *PUBLIC_KEY*, *PK_EXPIRATION*, and *USERS* cannot be assigned values,
#    as they are reserved for internal use

# registry structure:
# { <IamServer>:
#    {
#       "base-url": <str>,
#       "admin-id": <str>,
#       "admin-secret": <str>,
#       "client-id": <str>,
#       "client-secret": <str>,
#       "client-realm": <str,
#       "client-timeout": <int>,
#       "recipient-attr": <str>,
#       "public-key": <str>,
#       "pk-lifetime": <int>,
#       "pk-expiration": <int>,
#       "users": {}
#    },
#    ...
# }
# data in "users":
# {
#   "<user-id>": {
#      "access-token": <str>
#      "refresh-token": <str>
#      "access-expiration": <timestamp>,
#      "refresh-expiration": <timestamp>,
#      # transient attributes
#      "login-expiration": <timestamp>,
#      "login-id": <str>,
#      "redirect-uri": <str>
#   },
#   ...
# }
_IAM_SERVERS: Final[dict[IamServer, dict[IamParam, Any]]] = {}


# the lock protecting the data in '_IAM_SERVERS'
# (because it is 'Final' and set at declaration time, it can be accessed through simple imports)
_iam_lock: Final[RLock] = RLock()


def _iam_server_from_endpoint(endpoint: str,
                              errors: list[str] | None,
                              logger: Logger | None) -> IamServer | None:
    """
    Retrieve the registered *IAM* server associated with the service's invocation *endpoint*.

    :param endpoint: the service's invocation endpoint
    :param errors: incidental error messages
    :param logger: optional logger
    :return: the corresponding *IAM* server, or *None* if one could not be obtained
    """
    # initialize the return variable
    result: IamServer | None = None

    for iam_server in _IAM_SERVERS:
        if endpoint.startswith(iam_server):
            result = iam_server
            break

    if not result:
        msg: str = f"Unable to find a IAM server to service endpoint '{endpoint}'"
        if logger:
            logger.error(msg=msg)
        if isinstance(errors, list):
            errors.append(msg)

    return result


def _iam_server_from_issuer(issuer: str,
                            errors: list[str] | None,
                            logger: Logger | None) -> IamServer | None:
    """
    Retrieve the registered *IAM* server associated with the token's *issuer*.

    :param issuer: the token's issuer
    :param errors: incidental error messages
    :param logger: optional logger
    :return: the corresponding *IAM* server, or *None* if one could not be obtained
    """
    # initialize the return variable
    result: IamServer | None = None

    for iam_server, registry in _IAM_SERVERS.items():
        base_url: str = f"{registry[IamParam.URL_BASE]}/realms/{registry[IamParam.CLIENT_REALM]}"
        if base_url == issuer:
            result = IamServer(iam_server)
            break

    if not result:
        msg: str = f"Unable to find a IAM server associated with token issuer '{issuer}'"
        if logger:
            logger.error(msg=msg)
        if isinstance(errors, list):
            errors.append(msg)

    return result


def _get_public_key(iam_server: IamServer,
                    errors: list[str] | None,
                    logger: Logger | None) -> str:
    """
    Obtain the public key used by *iam_server* to sign the authentication tokens.

    This is accomplished by requesting the token issuer for its *JWKS* (JSON Web Key Set),
    containing the public keys used for various purposes, as indicated in the attribute *use*:
        - *enc*: the key is intended for encryption
        - *sig*: the key is intended for digital signature
        - *wrap*: the key is intended for key wrapping

    A typical JWKS set has the following format (for simplicity, 'n' and 'x5c' are truncated):
        {
            "keys": [
                {
                    "kid": "X2QEcSQ4Tg2M2EK6s2nhRHZH_GwD_zxZtiWVwP4S0tg",
                    "kty": "RSA",
                    "alg": "RSA256",
                    "use": "sig",
                    "n": "tQmDmyM3tMFt5FMVMbqbQYpaDPf6A5l4e_kTVDBiHrK_bRlGfkk8hYm5SNzNzCZ...",
                    "e": "AQAB",
                    "x5c": [
                        "MIIClzCCAX8CBgGZY0bqrTANBgkqhkiG9w0BAQsFADAPMQ0wCwYDVQQDDARpanVk..."
                    ],
                    "x5t": "MHfVp4kBjEZuYOtiaaGsfLCL15Q",
                    "x5t#S256": "QADezSLgD8emuonBz8hn8ghTnxo7AHX4NVNkr4luEhk"
                },
                ...
            ]
        }

    Once the signature key is obtained, it is converted from its original *JWK* (JSON Web Key) format
    to *PEM* (Privacy-Enhanced Mail) format. The public key is saved in *iam_server*'s registry.

    :param iam_server: the reference registered *IAM* server
    :param errors: incidental error messages
    :param logger: optional logger
    :return: the public key in *PEM* format, or *None* if error
    """
    # initialize the return variable
    result: str | None = None

    registry: dict[str, Any] = _get_iam_registry(iam_server=iam_server,
                                                 errors=errors,
                                                 logger=logger)
    if registry:
        now: int = int(datetime.now(tz=TZ_LOCAL).timestamp())
        if now > registry[IamParam.PK_EXPIRATION]:
            # obtain the JWKS (JSON Web Key Set) from the token issuer
            base_url: str = f"{registry[IamParam.URL_BASE]}/realms/{registry[IamParam.CLIENT_REALM]}"
            url: str = f"{base_url}/protocol/openid-connect/certs"
            if logger:
                logger.debug(msg=f"Obtaining signature public key used by IAM server '{iam_server}'")
                logger.debug(msg=f"GET {url}")
            try:
                response: requests.Response = requests.get(url=url)
                if response.status_code == 200:
                    # request succeeded
                    if logger:
                        logger.debug(msg=f"GET success, status {response.status_code}")
                    # select the appropriate JWK
                    reply: dict[str, list[dict[str, str]]] = response.json()
                    jwk: dict[str, str] | None = None
                    for key in reply["keys"]:
                        if key.get("use") == "sig":
                            jwk = key
                            break
                    if jwk:
                        # convert from 'JWK' to 'PEM' and save it for further use
                        result = crypto_jwk_convert(jwk=jwk,
                                                    fmt="PEM")
                        registry[IamParam.PUBLIC_KEY] = result
                        lifetime: int = registry[IamParam.PK_LIFETIME] or 0
                        registry[IamParam.PK_EXPIRATION] = now + lifetime if lifetime else sys.maxsize
                        if logger:
                            logger.debug("Public key obtained and saved")
                    else:
                        msg = "Signature public key missing from the token issuer's JWKS"
                        if logger:
                            logger.error(msg=msg)
                        if isinstance(errors, list):
                            errors.append(msg)
                elif logger:
                    msg: str = f"GET failure, status {response.status_code}, reason {response.reason}"
                    if hasattr(response, "content") and response.content:
                        msg += f", content {response.content}"
                    logger.error(msg=msg)
                    if isinstance(errors, list):
                        errors.append(msg)
            except Exception as e:
                # the operation raised an exception
                msg = exc_format(exc=e,
                                 exc_info=sys.exc_info())
                if logger:
                    logger.error(msg=msg)
                if isinstance(errors, list):
                    errors.append(msg)
        else:
            result = registry[IamParam.PUBLIC_KEY]

    return result


def _get_login_timeout(iam_server: IamServer,
                       errors: list[str] | None,
                       logger: Logger) -> int | None:
    """
    Retrieve the timeout currently applicable for the login operation.

    :param iam_server: the reference registered *IAM* server
    :param errors: incidental error messages
    :param logger: optional logger
    :return: the current login timeout, or *None* if the server is unknown or none has been set.
    """
    # initialize the return variable
    result: int | None = None

    registry: dict[str, Any] = _get_iam_registry(iam_server=iam_server,
                                                 errors=errors,
                                                 logger=logger)
    if registry:
        timeout: int = registry.get("client-timeout")
        if isinstance(timeout, int) and timeout > 0:
            result = timeout

    return result


def _get_user_data(iam_server: IamServer,
                   user_id: str,
                   errors: list[str] | None,
                   logger: Logger | None) -> dict[str, Any] | None:
    """
    Retrieve the data for *user_id* from *iam_server*'s registry.

    If an entry is not found for *user_id* in the registry, it is created.
    It will remain there until the user is logged out.

    :param iam_server: the reference registered *IAM* server
    :param errors: incidental error messages
    :param logger: optional logger
    :return: the data for *user_id* in *iam_server*'s registry, or *None* if the server is unknown
    """
    # initialize the return variable
    result: dict[str, Any] | None = None

    users: dict[str, dict[str, Any]] = _get_iam_users(iam_server=iam_server,
                                                      errors=errors,
                                                      logger=logger)
    if isinstance(users, dict):
        result = users.get(user_id)
        if not result:
            result = {
                UserParam.ACCESS_TOKEN: None,
                UserParam.REFRESH_TOKEN: None,
                UserParam.ACCESS_EXPIRATION: int(datetime.now(tz=TZ_LOCAL).timestamp()),
                UserParam.REFRESH_EXPIRATION: sys.maxsize
            }
            users[user_id] = result
            if logger:
                logger.debug(msg=f"Entry for '{user_id}' added to {iam_server}'s registry")
        elif logger:
            logger.debug(msg=f"Entry for '{user_id}' obtained from {iam_server}'s registry")

    return result


def _get_iam_registry(iam_server: IamServer,
                      errors: list[str] | None,
                      logger: Logger | None) -> dict[str, Any]:
    """
    Retrieve the registry associated with *iam_server*.

    :param iam_server: the reference registered *IAM* server
    :param errors: incidental error messages
    :param logger: optional logger
    :return: the registry associated with *iam_server*, or *None* if the server is unknown
    """
    # assign the return variable
    result: dict[str, Any] = _IAM_SERVERS.get(iam_server)

    if not result:
        msg = f"Unknown IAM server '{iam_server}'"
        if logger:
            logger.error(msg=msg)
        if isinstance(errors, list):
            errors.append(msg)

    return result


def _get_iam_users(iam_server: IamServer,
                   errors: list[str] | None,
                   logger: Logger | None) -> dict[str, dict[str, Any]]:
    """
    Retrieve the users data storage in *iam_server*'s registry.

    :param iam_server: the reference registered *IAM* server
    :param errors: incidental error messages
    :param logger: optional logger
    :return: the users data storage in *iam_server*'s registry, or *None* if the server is unknown
    """
    registry: dict[str, Any] = _get_iam_registry(iam_server=iam_server,
                                                 errors=errors,
                                                 logger=logger)
    return registry[IamParam.USERS] if registry else None
