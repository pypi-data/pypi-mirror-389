from http import HTTPStatus
from typing import Any, Dict, List, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.permission_public import PermissionPublic
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    skip: Union[Unset, int] = 0,
    limit: Union[Unset, int] = 100,
    resource: Union[None, Unset, str] = UNSET,
    action: Union[None, Unset, str] = UNSET,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {}

    params["skip"] = skip

    params["limit"] = limit

    json_resource: Union[None, Unset, str]
    if isinstance(resource, Unset):
        json_resource = UNSET
    else:
        json_resource = resource
    params["resource"] = json_resource

    json_action: Union[None, Unset, str]
    if isinstance(action, Unset):
        json_action = UNSET
    else:
        json_action = action
    params["action"] = json_action

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: Dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/rbac/permissions",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[HTTPValidationError, List["PermissionPublic"]]]:
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
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[HTTPValidationError, List["PermissionPublic"]]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    skip: Union[Unset, int] = 0,
    limit: Union[Unset, int] = 100,
    resource: Union[None, Unset, str] = UNSET,
    action: Union[None, Unset, str] = UNSET,
) -> Response[Union[HTTPValidationError, List["PermissionPublic"]]]:
    """获取权限列表

     获取所有系统权限列表。

    Args:
        skip (Union[Unset, int]): 跳过的记录数 Default: 0.
        limit (Union[Unset, int]): 返回的最大记录数 Default: 100.
        resource (Union[None, Unset, str]): 按资源筛选
        action (Union[None, Unset, str]): 按操作筛选

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, List['PermissionPublic']]]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        resource=resource,
        action=action,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    skip: Union[Unset, int] = 0,
    limit: Union[Unset, int] = 100,
    resource: Union[None, Unset, str] = UNSET,
    action: Union[None, Unset, str] = UNSET,
) -> Optional[Union[HTTPValidationError, List["PermissionPublic"]]]:
    """获取权限列表

     获取所有系统权限列表。

    Args:
        skip (Union[Unset, int]): 跳过的记录数 Default: 0.
        limit (Union[Unset, int]): 返回的最大记录数 Default: 100.
        resource (Union[None, Unset, str]): 按资源筛选
        action (Union[None, Unset, str]): 按操作筛选

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, List['PermissionPublic']]
    """

    return sync_detailed(
        client=client,
        skip=skip,
        limit=limit,
        resource=resource,
        action=action,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    skip: Union[Unset, int] = 0,
    limit: Union[Unset, int] = 100,
    resource: Union[None, Unset, str] = UNSET,
    action: Union[None, Unset, str] = UNSET,
) -> Response[Union[HTTPValidationError, List["PermissionPublic"]]]:
    """获取权限列表

     获取所有系统权限列表。

    Args:
        skip (Union[Unset, int]): 跳过的记录数 Default: 0.
        limit (Union[Unset, int]): 返回的最大记录数 Default: 100.
        resource (Union[None, Unset, str]): 按资源筛选
        action (Union[None, Unset, str]): 按操作筛选

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, List['PermissionPublic']]]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        resource=resource,
        action=action,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    skip: Union[Unset, int] = 0,
    limit: Union[Unset, int] = 100,
    resource: Union[None, Unset, str] = UNSET,
    action: Union[None, Unset, str] = UNSET,
) -> Optional[Union[HTTPValidationError, List["PermissionPublic"]]]:
    """获取权限列表

     获取所有系统权限列表。

    Args:
        skip (Union[Unset, int]): 跳过的记录数 Default: 0.
        limit (Union[Unset, int]): 返回的最大记录数 Default: 100.
        resource (Union[None, Unset, str]): 按资源筛选
        action (Union[None, Unset, str]): 按操作筛选

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, List['PermissionPublic']]
    """

    return (
        await asyncio_detailed(
            client=client,
            skip=skip,
            limit=limit,
            resource=resource,
            action=action,
        )
    ).parsed
