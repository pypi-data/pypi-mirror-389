from http import HTTPStatus
from typing import Any, Dict, Optional, Union
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.permission_public import PermissionPublic
from ...types import Response


def _get_kwargs(
    permission_id: UUID,
) -> Dict[str, Any]:
    _kwargs: Dict[str, Any] = {
        "method": "get",
        "url": f"/api/v1/rbac/permissions/{permission_id}",
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[HTTPValidationError, PermissionPublic]]:
    if response.status_code == 200:
        response_200 = PermissionPublic.from_dict(response.json())

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
) -> Response[Union[HTTPValidationError, PermissionPublic]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    permission_id: UUID,
    *,
    client: AuthenticatedClient,
) -> Response[Union[HTTPValidationError, PermissionPublic]]:
    """获取权限详情

     根据ID获取权限的详细信息。

    Args:
        permission_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, PermissionPublic]]
    """

    kwargs = _get_kwargs(
        permission_id=permission_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    permission_id: UUID,
    *,
    client: AuthenticatedClient,
) -> Optional[Union[HTTPValidationError, PermissionPublic]]:
    """获取权限详情

     根据ID获取权限的详细信息。

    Args:
        permission_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, PermissionPublic]
    """

    return sync_detailed(
        permission_id=permission_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    permission_id: UUID,
    *,
    client: AuthenticatedClient,
) -> Response[Union[HTTPValidationError, PermissionPublic]]:
    """获取权限详情

     根据ID获取权限的详细信息。

    Args:
        permission_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, PermissionPublic]]
    """

    kwargs = _get_kwargs(
        permission_id=permission_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    permission_id: UUID,
    *,
    client: AuthenticatedClient,
) -> Optional[Union[HTTPValidationError, PermissionPublic]]:
    """获取权限详情

     根据ID获取权限的详细信息。

    Args:
        permission_id (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, PermissionPublic]
    """

    return (
        await asyncio_detailed(
            permission_id=permission_id,
            client=client,
        )
    ).parsed
