from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.tenant_apps_response import TenantAppsResponse
from ...types import Response


def _get_kwargs(
    tenant_code: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/api/v1/multi-tenant/tenants/{tenant_code}/apps",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | TenantAppsResponse | None:
    if response.status_code == 200:
        response_200 = TenantAppsResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | TenantAppsResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    tenant_code: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[HTTPValidationError | TenantAppsResponse]:
    """Get Tenant Apps

     获取租户可用的应用列表

    Args:
        tenant_code (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TenantAppsResponse]
    """

    kwargs = _get_kwargs(
        tenant_code=tenant_code,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    tenant_code: str,
    *,
    client: AuthenticatedClient | Client,
) -> HTTPValidationError | TenantAppsResponse | None:
    """Get Tenant Apps

     获取租户可用的应用列表

    Args:
        tenant_code (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TenantAppsResponse
    """

    return sync_detailed(
        tenant_code=tenant_code,
        client=client,
    ).parsed


async def asyncio_detailed(
    tenant_code: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[HTTPValidationError | TenantAppsResponse]:
    """Get Tenant Apps

     获取租户可用的应用列表

    Args:
        tenant_code (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | TenantAppsResponse]
    """

    kwargs = _get_kwargs(
        tenant_code=tenant_code,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    tenant_code: str,
    *,
    client: AuthenticatedClient | Client,
) -> HTTPValidationError | TenantAppsResponse | None:
    """Get Tenant Apps

     获取租户可用的应用列表

    Args:
        tenant_code (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | TenantAppsResponse
    """

    return (
        await asyncio_detailed(
            tenant_code=tenant_code,
            client=client,
        )
    ).parsed
