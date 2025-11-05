from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.api_response import ApiResponse
from ...models.error_response import ErrorResponse
from ...models.upload_camera_settings_body import UploadCameraSettingsBody
from ...types import Response


def _get_kwargs(
    camera_id: str,
    *,
    body: UploadCameraSettingsBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/api/cameras/{camera_id}/settings/upload",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ApiResponse | ErrorResponse | None:
    if response.status_code == 200:
        response_200 = ApiResponse.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = ErrorResponse.from_dict(response.json())

        return response_400

    if response.status_code == 404:
        response_404 = ErrorResponse.from_dict(response.json())

        return response_404

    if response.status_code == 500:
        response_500 = ErrorResponse.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ApiResponse | ErrorResponse]:
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
    body: UploadCameraSettingsBody,
) -> Response[ApiResponse | ErrorResponse]:
    """Upload camera settings

     Load camera settings from PC file to camera

    Args:
        camera_id (str):
        body (UploadCameraSettingsBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiResponse | ErrorResponse]
    """

    kwargs = _get_kwargs(
        camera_id=camera_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    camera_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: UploadCameraSettingsBody,
) -> ApiResponse | ErrorResponse | None:
    """Upload camera settings

     Load camera settings from PC file to camera

    Args:
        camera_id (str):
        body (UploadCameraSettingsBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiResponse | ErrorResponse
    """

    return sync_detailed(
        camera_id=camera_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    camera_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: UploadCameraSettingsBody,
) -> Response[ApiResponse | ErrorResponse]:
    """Upload camera settings

     Load camera settings from PC file to camera

    Args:
        camera_id (str):
        body (UploadCameraSettingsBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiResponse | ErrorResponse]
    """

    kwargs = _get_kwargs(
        camera_id=camera_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    camera_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: UploadCameraSettingsBody,
) -> ApiResponse | ErrorResponse | None:
    """Upload camera settings

     Load camera settings from PC file to camera

    Args:
        camera_id (str):
        body (UploadCameraSettingsBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiResponse | ErrorResponse
    """

    return (
        await asyncio_detailed(
            camera_id=camera_id,
            client=client,
            body=body,
        )
    ).parsed
