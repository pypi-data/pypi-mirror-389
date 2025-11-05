from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error_response import ErrorResponse
from ...models.list_camera_settings_response_200 import ListCameraSettingsResponse200
from ...types import Response


def _get_kwargs(
    camera_id: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/api/cameras/{camera_id}/settings/files",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | ListCameraSettingsResponse200 | None:
    if response.status_code == 200:
        response_200 = ListCameraSettingsResponse200.from_dict(response.json())

        return response_200

    if response.status_code == 500:
        response_500 = ErrorResponse.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ErrorResponse | ListCameraSettingsResponse200]:
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
) -> Response[ErrorResponse | ListCameraSettingsResponse200]:
    """List saved settings files

     List all saved camera settings files on PC

    Args:
        camera_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorResponse | ListCameraSettingsResponse200]
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
) -> ErrorResponse | ListCameraSettingsResponse200 | None:
    """List saved settings files

     List all saved camera settings files on PC

    Args:
        camera_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorResponse | ListCameraSettingsResponse200
    """

    return sync_detailed(
        camera_id=camera_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    camera_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[ErrorResponse | ListCameraSettingsResponse200]:
    """List saved settings files

     List all saved camera settings files on PC

    Args:
        camera_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorResponse | ListCameraSettingsResponse200]
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
) -> ErrorResponse | ListCameraSettingsResponse200 | None:
    """List saved settings files

     List all saved camera settings files on PC

    Args:
        camera_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorResponse | ListCameraSettingsResponse200
    """

    return (
        await asyncio_detailed(
            camera_id=camera_id,
            client=client,
        )
    ).parsed
