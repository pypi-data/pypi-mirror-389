from http import HTTPStatus
from typing import Any, Dict, Optional, Union
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.update_tenant_user_request import UpdateTenantUserRequest
from ...types import Response


def _get_kwargs(
    tenant_id: UUID,
    user_id: UUID,
    *,
    body: UpdateTenantUserRequest,
) -> Dict[str, Any]:
    headers: Dict[str, Any] = {}

    _kwargs: Dict[str, Any] = {
        "method": "patch",
        "url": f"/api/v1/tenants/{tenant_id}/users/{user_id}",
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Any, HTTPValidationError]]:
    if response.status_code == 200:
        response_200 = response.json()
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
) -> Response[Union[Any, HTTPValidationError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    tenant_id: UUID,
    user_id: UUID,
    *,
    client: AuthenticatedClient,
    body: UpdateTenantUserRequest,
) -> Response[Union[Any, HTTPValidationError]]:
    """Update Tenant User

     更新租户用户管理员状态

    Args:
        tenant_id (UUID):
        user_id (UUID):
        body (UpdateTenantUserRequest): 更新租户用户信息请求

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        tenant_id=tenant_id,
        user_id=user_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    tenant_id: UUID,
    user_id: UUID,
    *,
    client: AuthenticatedClient,
    body: UpdateTenantUserRequest,
) -> Optional[Union[Any, HTTPValidationError]]:
    """Update Tenant User

     更新租户用户管理员状态

    Args:
        tenant_id (UUID):
        user_id (UUID):
        body (UpdateTenantUserRequest): 更新租户用户信息请求

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, HTTPValidationError]
    """

    return sync_detailed(
        tenant_id=tenant_id,
        user_id=user_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    tenant_id: UUID,
    user_id: UUID,
    *,
    client: AuthenticatedClient,
    body: UpdateTenantUserRequest,
) -> Response[Union[Any, HTTPValidationError]]:
    """Update Tenant User

     更新租户用户管理员状态

    Args:
        tenant_id (UUID):
        user_id (UUID):
        body (UpdateTenantUserRequest): 更新租户用户信息请求

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        tenant_id=tenant_id,
        user_id=user_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    tenant_id: UUID,
    user_id: UUID,
    *,
    client: AuthenticatedClient,
    body: UpdateTenantUserRequest,
) -> Optional[Union[Any, HTTPValidationError]]:
    """Update Tenant User

     更新租户用户管理员状态

    Args:
        tenant_id (UUID):
        user_id (UUID):
        body (UpdateTenantUserRequest): 更新租户用户信息请求

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, HTTPValidationError]
    """

    return (
        await asyncio_detailed(
            tenant_id=tenant_id,
            user_id=user_id,
            client=client,
            body=body,
        )
    ).parsed
