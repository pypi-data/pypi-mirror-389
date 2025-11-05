from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.connection_response import ConnectionResponse
from ...types import Response


def _get_kwargs(
    camera_id: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/api/cameras/{camera_id}/connection",
    }

    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> ConnectionResponse | None:
    if response.status_code == 200:
        response_200 = ConnectionResponse.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[ConnectionResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    camera_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[ConnectionResponse]:
    """Get connection status

     Check if camera is connected

    Args:
        camera_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ConnectionResponse]
    """

    kwargs = _get_kwargs(
        camera_id=camera_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    camera_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> ConnectionResponse | None:
    """Get connection status

     Check if camera is connected

    Args:
        camera_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ConnectionResponse
    """

    return sync_detailed(
        camera_id=camera_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    camera_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[ConnectionResponse]:
    """Get connection status

     Check if camera is connected

    Args:
        camera_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ConnectionResponse]
    """

    kwargs = _get_kwargs(
        camera_id=camera_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    camera_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> ConnectionResponse | None:
    """Get connection status

     Check if camera is connected

    Args:
        camera_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ConnectionResponse
    """

    return (
        await asyncio_detailed(
            camera_id=camera_id,
            client=client,
        )
    ).parsed
