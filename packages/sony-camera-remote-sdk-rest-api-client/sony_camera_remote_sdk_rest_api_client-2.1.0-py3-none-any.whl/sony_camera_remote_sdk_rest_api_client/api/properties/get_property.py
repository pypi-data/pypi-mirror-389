from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error_response import ErrorResponse
from ...models.property_response import PropertyResponse
from ...types import Response


def _get_kwargs(
    camera_id: str,
    property_name: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/api/cameras/{camera_id}/properties/{property_name}",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | PropertyResponse | None:
    if response.status_code == 200:
        response_200 = PropertyResponse.from_dict(response.json())

        return response_200

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
) -> Response[ErrorResponse | PropertyResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    camera_id: str,
    property_name: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[ErrorResponse | PropertyResponse]:
    """Get property value

     Read current value of a camera property.

    Supported properties include: iso, aperture, shutter-speed, white-balance, focus-mode,
    focus-area, exposure-program-mode, drive-mode, image-quality, file-format, raw-compression,
    priority-key, still-image-store-destination, zoom-distance, and more.

    See API_DOCUMENTATION.md for complete property list and enum values.

    Args:
        camera_id (str):
        property_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorResponse | PropertyResponse]
    """

    kwargs = _get_kwargs(
        camera_id=camera_id,
        property_name=property_name,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    camera_id: str,
    property_name: str,
    *,
    client: AuthenticatedClient | Client,
) -> ErrorResponse | PropertyResponse | None:
    """Get property value

     Read current value of a camera property.

    Supported properties include: iso, aperture, shutter-speed, white-balance, focus-mode,
    focus-area, exposure-program-mode, drive-mode, image-quality, file-format, raw-compression,
    priority-key, still-image-store-destination, zoom-distance, and more.

    See API_DOCUMENTATION.md for complete property list and enum values.

    Args:
        camera_id (str):
        property_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorResponse | PropertyResponse
    """

    return sync_detailed(
        camera_id=camera_id,
        property_name=property_name,
        client=client,
    ).parsed


async def asyncio_detailed(
    camera_id: str,
    property_name: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[ErrorResponse | PropertyResponse]:
    """Get property value

     Read current value of a camera property.

    Supported properties include: iso, aperture, shutter-speed, white-balance, focus-mode,
    focus-area, exposure-program-mode, drive-mode, image-quality, file-format, raw-compression,
    priority-key, still-image-store-destination, zoom-distance, and more.

    See API_DOCUMENTATION.md for complete property list and enum values.

    Args:
        camera_id (str):
        property_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorResponse | PropertyResponse]
    """

    kwargs = _get_kwargs(
        camera_id=camera_id,
        property_name=property_name,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    camera_id: str,
    property_name: str,
    *,
    client: AuthenticatedClient | Client,
) -> ErrorResponse | PropertyResponse | None:
    """Get property value

     Read current value of a camera property.

    Supported properties include: iso, aperture, shutter-speed, white-balance, focus-mode,
    focus-area, exposure-program-mode, drive-mode, image-quality, file-format, raw-compression,
    priority-key, still-image-store-destination, zoom-distance, and more.

    See API_DOCUMENTATION.md for complete property list and enum values.

    Args:
        camera_id (str):
        property_name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorResponse | PropertyResponse
    """

    return (
        await asyncio_detailed(
            camera_id=camera_id,
            property_name=property_name,
            client=client,
        )
    ).parsed
