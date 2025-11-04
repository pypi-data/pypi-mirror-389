from flask import Flask
from logging import Logger
from pypomes_core import APP_PREFIX, env_get_int, env_get_str
from typing import Any

from .iam_common import (
    _IAM_SERVERS, IamServer, IamParam, _iam_lock
)
from .iam_actions import action_token
from .iam_services import (
    service_login, service_logout, service_callback, service_exchange, service_token
)


def iam_setup(flask_app: Flask,
              iam_server: IamServer,
              base_url: str,
              client_id: str,
              client_realm: str,
              client_secret: str | None,
              recipient_attribute: str,
              admin_id: str = None,
              admin_secret: str = None,
              login_timeout: int = None,
              public_key_lifetime: int = None,
              callback_endpoint: str = None,
              exchange_endpoint: str = None,
              login_endpoint: str = None,
              logout_endpoint: str = None,
              token_endpoint: str = None) -> None:
    """
    Establish the provided parameters for configuring the *IAM* server *iam_server*.

    The parameters *admin_id* and *admin_* are required only if administrative are task are planned.
    The optional parameter *client_timeout* refers to the maximum time in seconds allowed for the
    user to login at the *IAM* server's login page, and defaults to no time limit.

    The parameter *client_secret* is required in most requests to the *IAM* server. In the case
    it is not provided, but *admin_id* and *admin_secret* are, it is obtained from the *IAM* server itself
    the first time it is needed.

    :param flask_app: the Flask application
    :param iam_server: identifies the supported *IAM* server (currently, *jusbr* or *keycloak*)
    :param base_url: base URL to request services
    :param client_id: the client's identification with the *IAM* server
    :param client_realm: the client realm
    :param client_secret: the client's password with the *IAM* server
    :param recipient_attribute: attribute in the token's payload holding the token's subject
    :param admin_id: identifies the realm administrator
    :param admin_secret: password for the realm administrator
    :param login_timeout: timeout for login authentication (in seconds,defaults to no timeout)
    :param public_key_lifetime: how long to use *IAM* server's public key, before refreshing it (in seconds)
    :param callback_endpoint: endpoint for the callback from the front end
    :param exchange_endpoint: endpoint for requesting token exchange
    :param login_endpoint: endpoint for redirecting user to the *IAM* server's login page
    :param logout_endpoint: endpoint for terminating user access
    :param token_endpoint: endpoint for retrieving authentication token
    """

    # configure the Keycloak registry
    with _iam_lock:
        _IAM_SERVERS[iam_server] = {
            IamParam.URL_BASE: base_url,
            IamParam.CLIENT_ID: client_id,
            IamParam.CLIENT_REALM: client_realm,
            IamParam.CLIENT_SECRET: client_secret,
            IamParam.RECIPIENT_ATTR: recipient_attribute,
            IamParam.ADMIN_ID: admin_id,
            IamParam.ADMIN_SECRET: admin_secret,
            IamParam.LOGIN_TIMEOUT: login_timeout,
            IamParam.PK_LIFETIME: public_key_lifetime,
            IamParam.PK_EXPIRATION: 0,
            IamParam.PUBLIC_KEY: None,
            IamParam.USERS: {}
        }

    # establish the endpoints
    if callback_endpoint:
        flask_app.add_url_rule(rule=callback_endpoint,
                               endpoint=f"{iam_server}-callback",
                               view_func=service_callback,
                               methods=["GET"])
    if login_endpoint:
        flask_app.add_url_rule(rule=login_endpoint,
                               endpoint=f"{iam_server}-login",
                               view_func=service_login,
                               methods=["GET"])
    if logout_endpoint:
        flask_app.add_url_rule(rule=logout_endpoint,
                               endpoint=f"{iam_server}-logout",
                               view_func=service_logout,
                               methods=["GET"])
    if token_endpoint:
        flask_app.add_url_rule(rule=token_endpoint,
                               endpoint=f"{iam_server}-token",
                               view_func=service_token,
                               methods=["GET"])
    if exchange_endpoint:
        flask_app.add_url_rule(rule=exchange_endpoint,
                               endpoint=f"{iam_server}-exchange",
                               view_func=service_exchange,
                               methods=["POST"])


def iam_get_env_parameters(iam_prefix: str = None) -> dict[str, Any]:
    """
    Retrieve the set parameters for a *IAM* server from the environment.

    the parameters are returned ready to be used as a '**kwargs' parameter set in a call to *iam_setup()*,
    and sorted in the order appropriate to use them instead with a '*args' parameter set.

    :param iam_prefix: the prefix classifying the parameters
    :return: the sorted parameters classified by *prefix*
    """
    return {
        "base_url": env_get_str(key=f"{APP_PREFIX}_{iam_prefix}_URL_AUTH_BASE"),
        "client_id": env_get_str(key=f"{APP_PREFIX}_{iam_prefix}_CLIENT_ID"),
        "client_realm": env_get_str(key=f"{APP_PREFIX}_{iam_prefix}_CLIENT_REALM"),
        "client_secret": env_get_str(key=f"{APP_PREFIX}_{iam_prefix}_CLIENT_SECRET"),
        "recipient_attribute": env_get_str(key=f"{APP_PREFIX}_{iam_prefix}_RECIPIENT_ATTR"),
        "admin_id": env_get_str(key=f"{APP_PREFIX}_{iam_prefix}_ADMIN_ID"),
        "admin_secret": env_get_str(key=f"{APP_PREFIX}_{iam_prefix}_ADMIN_SECRET"),
        "login_timeout": env_get_str(key=f"{APP_PREFIX}_{iam_prefix}_LOGIN_TIMEOUT"),
        "public_key_lifetime": env_get_int(key=f"{APP_PREFIX}_{iam_prefix}_PUBLIC_KEY_LIFETIME"),
        "callback_endpoint": env_get_str(key=f"{APP_PREFIX}_{iam_prefix}_ENDPOINT_CALLBACK"),
        "exchange_endpoint": env_get_str(key=f"{APP_PREFIX}_{iam_prefix}_ENDPOINT_EXCHANGE"),
        "login_endpoint": env_get_str(key=f"{APP_PREFIX}_{iam_prefix}_ENDPOINT_LOGIN"),
        "logout_endpoint": env_get_str(key=f"{APP_PREFIX}_{iam_prefix}_ENDPOINT_LOGOUT"),
        "token_endpoint": env_get_str(key=f"{APP_PREFIX}_{iam_prefix}_ENDPOINT_TOKEN")
    }


def iam_get_token(iam_server: IamServer,
                  user_id: str,
                  errors: list[str] = None,
                  logger: Logger = None) -> str:
    """
    Retrieve an authentication token for *user_id*.

    :param iam_server: identifies the *IAM* server
    :param user_id: identifies the user
    :param errors: incidental errors
    :param logger: optional logger
    :return: the uthentication tokem
    """
    # declare the return variable
    result: str

    # retrieve the token
    args: dict[str, Any] = {"user-id": user_id}
    with _iam_lock:
        result = action_token(iam_server=iam_server,
                              args=args,
                              errors=errors,
                              logger=logger)
    return result
