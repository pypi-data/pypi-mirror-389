from http import HTTPStatus
from typing import Any, Dict, List, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.app_list_item import AppListItem
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    skip: Union[Unset, int] = 0,
    limit: Union[Unset, int] = 100,
    include_deleted: Union[Unset, bool] = False,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {}

    params["skip"] = skip

    params["limit"] = limit

    params["include_deleted"] = include_deleted

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: Dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/apps/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[HTTPValidationError, List["AppListItem"]]]:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = AppListItem.from_dict(response_200_item_data)

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
) -> Response[Union[HTTPValidationError, List["AppListItem"]]]:
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
    include_deleted: Union[Unset, bool] = False,
) -> Response[Union[HTTPValidationError, List["AppListItem"]]]:
    """获取应用列表

     获取所有未删除的应用列表，支持分页。不包含API密钥信息。

    Args:
        skip (Union[Unset, int]): 跳过的记录数 Default: 0.
        limit (Union[Unset, int]): 返回的最大记录数 Default: 100.
        include_deleted (Union[Unset, bool]): 是否包含已删除的应用 Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, List['AppListItem']]]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        include_deleted=include_deleted,
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
    include_deleted: Union[Unset, bool] = False,
) -> Optional[Union[HTTPValidationError, List["AppListItem"]]]:
    """获取应用列表

     获取所有未删除的应用列表，支持分页。不包含API密钥信息。

    Args:
        skip (Union[Unset, int]): 跳过的记录数 Default: 0.
        limit (Union[Unset, int]): 返回的最大记录数 Default: 100.
        include_deleted (Union[Unset, bool]): 是否包含已删除的应用 Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, List['AppListItem']]
    """

    return sync_detailed(
        client=client,
        skip=skip,
        limit=limit,
        include_deleted=include_deleted,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    skip: Union[Unset, int] = 0,
    limit: Union[Unset, int] = 100,
    include_deleted: Union[Unset, bool] = False,
) -> Response[Union[HTTPValidationError, List["AppListItem"]]]:
    """获取应用列表

     获取所有未删除的应用列表，支持分页。不包含API密钥信息。

    Args:
        skip (Union[Unset, int]): 跳过的记录数 Default: 0.
        limit (Union[Unset, int]): 返回的最大记录数 Default: 100.
        include_deleted (Union[Unset, bool]): 是否包含已删除的应用 Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, List['AppListItem']]]
    """

    kwargs = _get_kwargs(
        skip=skip,
        limit=limit,
        include_deleted=include_deleted,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    skip: Union[Unset, int] = 0,
    limit: Union[Unset, int] = 100,
    include_deleted: Union[Unset, bool] = False,
) -> Optional[Union[HTTPValidationError, List["AppListItem"]]]:
    """获取应用列表

     获取所有未删除的应用列表，支持分页。不包含API密钥信息。

    Args:
        skip (Union[Unset, int]): 跳过的记录数 Default: 0.
        limit (Union[Unset, int]): 返回的最大记录数 Default: 100.
        include_deleted (Union[Unset, bool]): 是否包含已删除的应用 Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, List['AppListItem']]
    """

    return (
        await asyncio_detailed(
            client=client,
            skip=skip,
            limit=limit,
            include_deleted=include_deleted,
        )
    ).parsed
