from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.role_public import RolePublic
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    skip: int | Unset = 0,
    limit: int | Unset = 100,
    app_id: None | Unset | UUID = UNSET,
    tenant_id: None | Unset | UUID = UNSET,
    include_deleted: bool | Unset = False,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["skip"] = skip

    params["limit"] = limit

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

    params["include_deleted"] = include_deleted

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/rbac/roles",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | list[RolePublic] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = RolePublic.from_dict(response_200_item_data)

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
) -> Response[HTTPValidationError | list[RolePublic]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    skip: int | Unset = 0,
    limit: int | Unset = 100,
    app_id: None | Unset | UUID = UNSET,
    tenant_id: None | Unset | UUID = UNSET,
    include_deleted: bool | Unset = False,
) -> Response[HTTPValidationError | list[RolePublic]]:
    """获取角色列表

     获取所有角色列表，支持按应用和租户筛选。

    Args:
        skip (int | Unset): 跳过的记录数 Default: 0.
        limit (int | Unset): 返回的最大记录数 Default: 100.
        app_id (None | Unset | UUID): 按应用ID筛选
        tenant_id (None | Unset | UUID): 按租户ID筛选
        include_deleted (bool | Unset): 是否包含已删除的角色 Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | list[RolePublic]]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        app_id=app_id,
        tenant_id=tenant_id,
        include_deleted=include_deleted,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    skip: int | Unset = 0,
    limit: int | Unset = 100,
    app_id: None | Unset | UUID = UNSET,
    tenant_id: None | Unset | UUID = UNSET,
    include_deleted: bool | Unset = False,
) -> HTTPValidationError | list[RolePublic] | None:
    """获取角色列表

     获取所有角色列表，支持按应用和租户筛选。

    Args:
        skip (int | Unset): 跳过的记录数 Default: 0.
        limit (int | Unset): 返回的最大记录数 Default: 100.
        app_id (None | Unset | UUID): 按应用ID筛选
        tenant_id (None | Unset | UUID): 按租户ID筛选
        include_deleted (bool | Unset): 是否包含已删除的角色 Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | list[RolePublic]
    """

    return sync_detailed(
        client=client,
        skip=skip,
        limit=limit,
        app_id=app_id,
        tenant_id=tenant_id,
        include_deleted=include_deleted,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    skip: int | Unset = 0,
    limit: int | Unset = 100,
    app_id: None | Unset | UUID = UNSET,
    tenant_id: None | Unset | UUID = UNSET,
    include_deleted: bool | Unset = False,
) -> Response[HTTPValidationError | list[RolePublic]]:
    """获取角色列表

     获取所有角色列表，支持按应用和租户筛选。

    Args:
        skip (int | Unset): 跳过的记录数 Default: 0.
        limit (int | Unset): 返回的最大记录数 Default: 100.
        app_id (None | Unset | UUID): 按应用ID筛选
        tenant_id (None | Unset | UUID): 按租户ID筛选
        include_deleted (bool | Unset): 是否包含已删除的角色 Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | list[RolePublic]]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        app_id=app_id,
        tenant_id=tenant_id,
        include_deleted=include_deleted,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    skip: int | Unset = 0,
    limit: int | Unset = 100,
    app_id: None | Unset | UUID = UNSET,
    tenant_id: None | Unset | UUID = UNSET,
    include_deleted: bool | Unset = False,
) -> HTTPValidationError | list[RolePublic] | None:
    """获取角色列表

     获取所有角色列表，支持按应用和租户筛选。

    Args:
        skip (int | Unset): 跳过的记录数 Default: 0.
        limit (int | Unset): 返回的最大记录数 Default: 100.
        app_id (None | Unset | UUID): 按应用ID筛选
        tenant_id (None | Unset | UUID): 按租户ID筛选
        include_deleted (bool | Unset): 是否包含已删除的角色 Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | list[RolePublic]
    """

    return (
        await asyncio_detailed(
            client=client,
            skip=skip,
            limit=limit,
            app_id=app_id,
            tenant_id=tenant_id,
            include_deleted=include_deleted,
        )
    ).parsed
