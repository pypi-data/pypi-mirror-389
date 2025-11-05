from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.permission_public import PermissionPublic
from ...types import UNSET, Response


def _get_kwargs(
    user_id: UUID,
    *,
    app_id: UUID,
    tenant_id: UUID,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_app_id = str(app_id)
    params["app_id"] = json_app_id

    json_tenant_id = str(tenant_id)
    params["tenant_id"] = json_tenant_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/api/v1/rbac/users/{user_id}/permissions",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | list[PermissionPublic] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = PermissionPublic.from_dict(response_200_item_data)

            response_200.append(response_200_item)

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
) -> Response[HTTPValidationError | list[PermissionPublic]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    user_id: UUID,
    *,
    client: AuthenticatedClient,
    app_id: UUID,
    tenant_id: UUID,
) -> Response[HTTPValidationError | list[PermissionPublic]]:
    """获取用户的所有权限

     获取用户通过角色获得的所有权限（在特定应用和租户中）。

    Args:
        user_id (UUID):
        app_id (UUID): 应用ID
        tenant_id (UUID): 租户ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | list[PermissionPublic]]
    """

    kwargs = _get_kwargs(
        user_id=user_id,
        app_id=app_id,
        tenant_id=tenant_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    user_id: UUID,
    *,
    client: AuthenticatedClient,
    app_id: UUID,
    tenant_id: UUID,
) -> HTTPValidationError | list[PermissionPublic] | None:
    """获取用户的所有权限

     获取用户通过角色获得的所有权限（在特定应用和租户中）。

    Args:
        user_id (UUID):
        app_id (UUID): 应用ID
        tenant_id (UUID): 租户ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | list[PermissionPublic]
    """

    return sync_detailed(
        user_id=user_id,
        client=client,
        app_id=app_id,
        tenant_id=tenant_id,
    ).parsed


async def asyncio_detailed(
    user_id: UUID,
    *,
    client: AuthenticatedClient,
    app_id: UUID,
    tenant_id: UUID,
) -> Response[HTTPValidationError | list[PermissionPublic]]:
    """获取用户的所有权限

     获取用户通过角色获得的所有权限（在特定应用和租户中）。

    Args:
        user_id (UUID):
        app_id (UUID): 应用ID
        tenant_id (UUID): 租户ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | list[PermissionPublic]]
    """

    kwargs = _get_kwargs(
        user_id=user_id,
        app_id=app_id,
        tenant_id=tenant_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    user_id: UUID,
    *,
    client: AuthenticatedClient,
    app_id: UUID,
    tenant_id: UUID,
) -> HTTPValidationError | list[PermissionPublic] | None:
    """获取用户的所有权限

     获取用户通过角色获得的所有权限（在特定应用和租户中）。

    Args:
        user_id (UUID):
        app_id (UUID): 应用ID
        tenant_id (UUID): 租户ID

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | list[PermissionPublic]
    """

    return (
        await asyncio_detailed(
            user_id=user_id,
            client=client,
            app_id=app_id,
            tenant_id=tenant_id,
        )
    ).parsed
