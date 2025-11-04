import json
import requests
import sys
from base64 import b64encode
from datetime import datetime
from enum import StrEnum
from logging import Logger
from pypomes_core import TZ_LOCAL, exc_format
from threading import Lock
from typing import Any, Final


class ProviderParam(StrEnum):
    """
    Parameters for configuring a *JWT* token provider.
    """
    URL = "url"
    USER = "user"
    PWD = "pwd"
    CUSTOM_AUTH = "custom-auth"
    HEADER_DATA = "headers-data"
    BODY_DATA = "body-data"
    ACCESS_TOKEN = "access-token"
    ACCESS_EXPIRATION = "access-expiration"
    REFRESH_TOKEN = "refresh-token"
    REFRESH_EXPIRATION = "refresh-expiration"


# structure:
# {
#    <provider-id>: {
#      "url": <strl>,
#      "user": <str>,
#      "pwd": <str>,
#      "custom-auth": <bool>,
#      "headers-data": <dict[str, str]>,
#      "body-data": <dict[str, str],
#      "access-token": <str>,
#      "access-expiration": <timestamp>,
#      "refresh-token": <str>,
#      "refresh-expiration": <timestamp>
#    }
# }
_provider_registry: Final[dict[str, dict[str, Any]]] = {}

# the lock protecting the data in '_provider_registry'
# (because it is 'Final' and set at declaration time, it can be accessed through simple imports)
_provider_lock: Final[Lock] = Lock()


def provider_register(provider_id: str,
                      auth_url: str,
                      auth_user: str,
                      auth_pwd: str,
                      custom_auth: tuple[str, str] = None,
                      headers_data: dict[str, str] = None,
                      body_data: dict[str, str] = None) -> None:
    """
    Register an external authentication token provider.

    If specified, *custom_auth* provides key names for sending credentials (username and password, in this order)
    as key-value pairs in the body of the request. Otherwise, the external provider *provider_id* uses the standard
    HTTP Basic Authorization scheme, wherein the credentials are B64-encoded and sent in the request headers.

    Optional constant key-value pairs (such as ['Content-Type', 'application/x-www-form-urlencoded']), to be
    added to the request headers, may be specified in *headers_data*. Likewise, optional constant key-value pairs
    (such as ['grant_type', 'client_credentials']), to be added to the request body, may be specified in *body_data*.

    :param provider_id: the provider's identification
    :param auth_url: the url to request authentication tokens with
    :param auth_user: the basic authorization user
    :param auth_pwd: the basic authorization password
    :param custom_auth: optional key names for sending the credentials as key-value pairs in the body of the request
    :param headers_data: optional key-value pairs to be added to the request headers
    :param body_data: optional key-value pairs to be added to the request body
    """
    global _provider_registry

    with _provider_lock:
        _provider_registry[provider_id] = {
            ProviderParam.URL: auth_url,
            ProviderParam.USER: auth_user,
            ProviderParam.PWD: auth_pwd,
            ProviderParam.CUSTOM_AUTH: custom_auth,
            ProviderParam.HEADER_DATA: headers_data,
            ProviderParam.BODY_DATA: body_data,
            ProviderParam.ACCESS_TOKEN: None,
            ProviderParam.ACCESS_EXPIRATION: 0,
            ProviderParam.REFRESH_TOKEN: None,
            ProviderParam.REFRESH_EXPIRATION: 0
        }


def provider_get_token(provider_id: str,
                       errors: list[str] = None,
                       logger: Logger = None) -> str | None:
    """
    Obtain an authentication token from the external provider *provider_id*.

    :param provider_id: the provider's identification
    :param errors: incidental error messages
    :param logger: optional logger
    """
    global _provider_registry  # noqa: PLW0602

    # initialize the return variable
    result: str | None = None

    with _provider_lock:
        provider: dict[str, Any] = _provider_registry.get(provider_id)
        if provider:
            now: int = int(datetime.now(tz=TZ_LOCAL).timestamp())
            if now < provider.get(ProviderParam.ACCESS_EXPIRATION):
                # retrieve the stored access token
                result = provider.get(ProviderParam.ACCESS_TOKEN)
            else:
                # access token has expired
                header_data: dict[str, str] | None = None
                body_data: dict[str, str] | None = None
                url: str = provider.get(ProviderParam.URL)
                refresh_token: str = provider.get(ProviderParam.REFRESH_TOKEN)
                if refresh_token:
                    # refresh token exists
                    refresh_expiration: int = provider.get(ProviderParam.REFRESH_EXPIRATION)
                    if now < refresh_expiration:
                        # refresh token has not expired
                        header_data: dict[str, str] = {
                            "Content-Type": "application/json"
                        }
                        body_data: dict[str, str] = {
                            "grant_type": "refresh_token",
                            "refresh_token": refresh_token
                        }
                if not body_data:
                    # refresh token does not exist or has expired
                    user: str = provider.get(ProviderParam.USER)
                    pwd: str = provider.get(ProviderParam.PWD)
                    headers_data: dict[str, str] = provider.get(ProviderParam.HEADER_DATA) or {}
                    body_data: dict[str, str] = provider.get(ProviderParam.BODY_DATA) or {}
                    custom_auth: tuple[str, str] = provider.get(ProviderParam.CUSTOM_AUTH)
                    if custom_auth:
                        body_data[custom_auth[0]] = user
                        body_data[custom_auth[1]] = pwd
                    else:
                        enc_bytes: bytes = b64encode(f"{user}:{pwd}".encode())
                        headers_data["Authorization"] = f"Basic {enc_bytes.decode()}"

                # obtain the token
                token_data: dict[str, Any] = __post_for_token(url=url,
                                                              header_data=header_data,
                                                              body_data=body_data,
                                                              errors=errors,
                                                              logger=logger)
                if token_data:
                    result = token_data.get("access_token")
                    provider[ProviderParam.ACCESS_TOKEN] = result
                    provider[ProviderParam.ACCESS_EXPIRATION] = now + token_data.get("expires_in")
                    refresh_token = token_data.get("refresh_token")
                    if refresh_token:
                        provider[ProviderParam.REFRESH_TOKEN] = refresh_token
                        refresh_exp: int = token_data.get("refresh_expires_in")
                        provider[ProviderParam.REFRESH_EXPIRATION] = (now + refresh_exp) \
                            if refresh_exp else sys.maxsize

        elif logger or isinstance(errors, list):
            msg: str = f"Unknown provider '{provider_id}'"
            if logger:
                logger.error(msg=msg)
            if isinstance(errors, list):
                errors.append(msg)

    return result


def __post_for_token(url: str,
                     header_data: dict[str, str],
                     body_data: dict[str, Any],
                     errors: list[str] | None,
                     logger: Logger | None) -> dict[str, Any] | None:
    """
    Send a *POST* request to *url* and return the token data obtained.

    Token acquisition and token refresh are the two types of requests contemplated herein.
    For the former, *header_data* and *body_data* will have contents customized to the specific provider,
    whereas the latter's *body_data* will contain these two attributes:
        - "grant_type": "refresh_token"
        - "refresh_token": <current-refresh-token>

    The typical data set returned contains the following attributes:
        {
            "token_type": "Bearer",
            "access_token": <str>,
            "expires_in": <number-of-seconds>,
            "refresh_token": <str>,
            "refesh_expires_in": <number-of-seconds>
        }

    :param url: the target URL
    :param header_data: the data to send in the header of the request
    :param body_data: the data to send in the body of the request
    :param errors: incidental errors
    :param logger: optional logger
    :return: the token data, or *None* if error
    """
    # initialize the return variable
    result: dict[str, Any] | None = None

    # log the POST
    if logger:
        logger.debug(msg=f"POST {url}, {json.dumps(obj=body_data,
                                                   ensure_ascii=False)}")
    try:
        response: requests.Response = requests.post(url=url,
                                                    data=body_data,
                                                    headers=header_data,
                                                    timeout=None)
        if response.status_code == 200:
            # request succeeded
            result = response.json()
            if logger:
                logger.debug(msg=f"POST success, status {response.status_code}")
        else:
            # request failed, report the problem
            msg: str = (f"POST failure, "
                        f"status {response.status_code}, reason {response.reason}")
            if hasattr(response, "content") and response.content:
                msg += f", content '{response.content}'"
            if logger:
                logger.error(msg=msg)
            if isinstance(errors, list):
                errors.append(msg)
    except Exception as e:
        # the operation raised an exception
        err_msg = exc_format(exc=e,
                             exc_info=sys.exc_info())
        msg: str = f"POST error, {err_msg}"
        if logger:
            logger.debug(msg=msg)
        if isinstance(errors, list):
            errors.append(msg)

    return result
