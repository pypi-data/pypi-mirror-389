from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.app_response import AppResponse
from ...models.http_validation_error import HTTPValidationError
from ...models.update_app_request import UpdateAppRequest
from ...types import Response


def _get_kwargs(
    app_id: UUID,
    *,
    body: UpdateAppRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": f"/api/v1/apps/{app_id}",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> AppResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = AppResponse.from_dict(response.json())

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
) -> Response[AppResponse | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    app_id: UUID,
    *,
    client: AuthenticatedClient,
    body: UpdateAppRequest,
) -> Response[AppResponse | HTTPValidationError]:
    """更新应用

     更新应用信息（不包括API密钥，如需更新密钥请使用重新生成接口）。

    Args:
        app_id (UUID):
        body (UpdateAppRequest): 更新应用请求

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AppResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        app_id=app_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    app_id: UUID,
    *,
    client: AuthenticatedClient,
    body: UpdateAppRequest,
) -> AppResponse | HTTPValidationError | None:
    """更新应用

     更新应用信息（不包括API密钥，如需更新密钥请使用重新生成接口）。

    Args:
        app_id (UUID):
        body (UpdateAppRequest): 更新应用请求

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AppResponse | HTTPValidationError
    """

    return sync_detailed(
        app_id=app_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    app_id: UUID,
    *,
    client: AuthenticatedClient,
    body: UpdateAppRequest,
) -> Response[AppResponse | HTTPValidationError]:
    """更新应用

     更新应用信息（不包括API密钥，如需更新密钥请使用重新生成接口）。

    Args:
        app_id (UUID):
        body (UpdateAppRequest): 更新应用请求

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AppResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        app_id=app_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    app_id: UUID,
    *,
    client: AuthenticatedClient,
    body: UpdateAppRequest,
) -> AppResponse | HTTPValidationError | None:
    """更新应用

     更新应用信息（不包括API密钥，如需更新密钥请使用重新生成接口）。

    Args:
        app_id (UUID):
        body (UpdateAppRequest): 更新应用请求

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AppResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            app_id=app_id,
            client=client,
            body=body,
        )
    ).parsed
