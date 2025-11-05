from http import HTTPStatus
from typing import Any, Dict, Optional, Union
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.add_permission_to_role_request import AddPermissionToRoleRequest
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    role_id: UUID,
    *,
    body: AddPermissionToRoleRequest,
) -> Dict[str, Any]:
    headers: Dict[str, Any] = {}

    _kwargs: Dict[str, Any] = {
        "method": "post",
        "url": f"/api/v1/rbac/roles/{role_id}/permissions",
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Any, HTTPValidationError]]:
    if response.status_code == 201:
        response_201 = response.json()
        return response_201
    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[Any, HTTPValidationError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    role_id: UUID,
    *,
    client: AuthenticatedClient,
    body: AddPermissionToRoleRequest,
) -> Response[Union[Any, HTTPValidationError]]:
    """为角色添加权限

     为指定角色添加权限。

    Args:
        role_id (UUID):
        body (AddPermissionToRoleRequest): 为角色添加权限请求

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        role_id=role_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    role_id: UUID,
    *,
    client: AuthenticatedClient,
    body: AddPermissionToRoleRequest,
) -> Optional[Union[Any, HTTPValidationError]]:
    """为角色添加权限

     为指定角色添加权限。

    Args:
        role_id (UUID):
        body (AddPermissionToRoleRequest): 为角色添加权限请求

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, HTTPValidationError]
    """

    return sync_detailed(
        role_id=role_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    role_id: UUID,
    *,
    client: AuthenticatedClient,
    body: AddPermissionToRoleRequest,
) -> Response[Union[Any, HTTPValidationError]]:
    """为角色添加权限

     为指定角色添加权限。

    Args:
        role_id (UUID):
        body (AddPermissionToRoleRequest): 为角色添加权限请求

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        role_id=role_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    role_id: UUID,
    *,
    client: AuthenticatedClient,
    body: AddPermissionToRoleRequest,
) -> Optional[Union[Any, HTTPValidationError]]:
    """为角色添加权限

     为指定角色添加权限。

    Args:
        role_id (UUID):
        body (AddPermissionToRoleRequest): 为角色添加权限请求

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, HTTPValidationError]
    """

    return (
        await asyncio_detailed(
            role_id=role_id,
            client=client,
            body=body,
        )
    ).parsed
