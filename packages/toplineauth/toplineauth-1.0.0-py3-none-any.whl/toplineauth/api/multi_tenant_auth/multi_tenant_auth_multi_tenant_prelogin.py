from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.prelogin_request import PreloginRequest
from ...models.prelogin_response import PreloginResponse
from ...types import Response


def _get_kwargs(
    *,
    body: PreloginRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/multi-tenant/prelogin",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | PreloginResponse | None:
    if response.status_code == 200:
        response_200 = PreloginResponse.from_dict(response.json())

        return response_200

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[HTTPValidationError | PreloginResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: PreloginRequest,
) -> Response[HTTPValidationError | PreloginResponse]:
    """Multi Tenant Prelogin

     预登录（两步式登录的第一步）
    - 验证邮箱/密码
    - 根据 app_id 列出用户可进入的租户候选
    - 无论候选数量多少，统一要求用户进行租户选择

    Args:
        body (PreloginRequest): 预登录请求：用户在特定应用下登录，但尚未确定租户（使用 ID）

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | PreloginResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: PreloginRequest,
) -> HTTPValidationError | PreloginResponse | None:
    """Multi Tenant Prelogin

     预登录（两步式登录的第一步）
    - 验证邮箱/密码
    - 根据 app_id 列出用户可进入的租户候选
    - 无论候选数量多少，统一要求用户进行租户选择

    Args:
        body (PreloginRequest): 预登录请求：用户在特定应用下登录，但尚未确定租户（使用 ID）

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | PreloginResponse
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: PreloginRequest,
) -> Response[HTTPValidationError | PreloginResponse]:
    """Multi Tenant Prelogin

     预登录（两步式登录的第一步）
    - 验证邮箱/密码
    - 根据 app_id 列出用户可进入的租户候选
    - 无论候选数量多少，统一要求用户进行租户选择

    Args:
        body (PreloginRequest): 预登录请求：用户在特定应用下登录，但尚未确定租户（使用 ID）

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | PreloginResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: PreloginRequest,
) -> HTTPValidationError | PreloginResponse | None:
    """Multi Tenant Prelogin

     预登录（两步式登录的第一步）
    - 验证邮箱/密码
    - 根据 app_id 列出用户可进入的租户候选
    - 无论候选数量多少，统一要求用户进行租户选择

    Args:
        body (PreloginRequest): 预登录请求：用户在特定应用下登录，但尚未确定租户（使用 ID）

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | PreloginResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
