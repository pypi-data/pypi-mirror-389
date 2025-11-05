from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.user_role_info import UserRoleInfo
from ...types import UNSET, Response, Unset


def _get_kwargs(
    user_id: UUID,
    *,
    app_id: None | Unset | UUID = UNSET,
    tenant_id: None | Unset | UUID = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_app_id: None | str | Unset
    if isinstance(app_id, Unset):
        json_app_id = UNSET
    elif isinstance(app_id, UUID):
        json_app_id = str(app_id)
    else:
        json_app_id = app_id
    params["app_id"] = json_app_id

    json_tenant_id: None | str | Unset
    if isinstance(tenant_id, Unset):
        json_tenant_id = UNSET
    elif isinstance(tenant_id, UUID):
        json_tenant_id = str(tenant_id)
    else:
        json_tenant_id = tenant_id
    params["tenant_id"] = json_tenant_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/api/v1/rbac/users/{user_id}/roles",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | list[UserRoleInfo] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = UserRoleInfo.from_dict(response_200_item_data)

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
) -> Response[HTTPValidationError | list[UserRoleInfo]]:
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
    app_id: None | Unset | UUID = UNSET,
    tenant_id: None | Unset | UUID = UNSET,
) -> Response[HTTPValidationError | list[UserRoleInfo]]:
    """获取用户的角色列表

     获取指定用户在所有应用和租户中的角色。

    Args:
        user_id (UUID):
        app_id (None | Unset | UUID): 按应用ID筛选
        tenant_id (None | Unset | UUID): 按租户ID筛选

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | list[UserRoleInfo]]
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
    app_id: None | Unset | UUID = UNSET,
    tenant_id: None | Unset | UUID = UNSET,
) -> HTTPValidationError | list[UserRoleInfo] | None:
    """获取用户的角色列表

     获取指定用户在所有应用和租户中的角色。

    Args:
        user_id (UUID):
        app_id (None | Unset | UUID): 按应用ID筛选
        tenant_id (None | Unset | UUID): 按租户ID筛选

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | list[UserRoleInfo]
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
    app_id: None | Unset | UUID = UNSET,
    tenant_id: None | Unset | UUID = UNSET,
) -> Response[HTTPValidationError | list[UserRoleInfo]]:
    """获取用户的角色列表

     获取指定用户在所有应用和租户中的角色。

    Args:
        user_id (UUID):
        app_id (None | Unset | UUID): 按应用ID筛选
        tenant_id (None | Unset | UUID): 按租户ID筛选

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | list[UserRoleInfo]]
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
    app_id: None | Unset | UUID = UNSET,
    tenant_id: None | Unset | UUID = UNSET,
) -> HTTPValidationError | list[UserRoleInfo] | None:
    """获取用户的角色列表

     获取指定用户在所有应用和租户中的角色。

    Args:
        user_id (UUID):
        app_id (None | Unset | UUID): 按应用ID筛选
        tenant_id (None | Unset | UUID): 按租户ID筛选

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | list[UserRoleInfo]
    """

    return (
        await asyncio_detailed(
            user_id=user_id,
            client=client,
            app_id=app_id,
            tenant_id=tenant_id,
        )
    ).parsed
