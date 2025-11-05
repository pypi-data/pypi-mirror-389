from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.download_sd_card_file_body import DownloadSDCardFileBody
from ...models.download_sd_card_file_response_200 import DownloadSDCardFileResponse200
from ...models.download_sd_card_file_slot import DownloadSDCardFileSlot
from ...models.error_response import ErrorResponse
from ...types import Response


def _get_kwargs(
    camera_id: str,
    slot: DownloadSDCardFileSlot,
    content_id: int,
    file_id: int,
    *,
    body: DownloadSDCardFileBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/api/cameras/{camera_id}/sd-card/slot/{slot}/files/{content_id}/{file_id}/download",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DownloadSDCardFileResponse200 | ErrorResponse | None:
    if response.status_code == 200:
        response_200 = DownloadSDCardFileResponse200.from_dict(response.json())

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
) -> Response[DownloadSDCardFileResponse200 | ErrorResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    camera_id: str,
    slot: DownloadSDCardFileSlot,
    content_id: int,
    file_id: int,
    *,
    client: AuthenticatedClient | Client,
    body: DownloadSDCardFileBody,
) -> Response[DownloadSDCardFileResponse200 | ErrorResponse]:
    """Download SD card file

     Download a specific file from the SD card to PC.

    **Requirements:**
    - Camera must be connected in `remote-transfer` or `contents-transfer` mode
    - Use content_id and file_id from the file list endpoint

    Args:
        camera_id (str):
        slot (DownloadSDCardFileSlot):
        content_id (int):
        file_id (int):
        body (DownloadSDCardFileBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DownloadSDCardFileResponse200 | ErrorResponse]
    """

    kwargs = _get_kwargs(
        camera_id=camera_id,
        slot=slot,
        content_id=content_id,
        file_id=file_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    camera_id: str,
    slot: DownloadSDCardFileSlot,
    content_id: int,
    file_id: int,
    *,
    client: AuthenticatedClient | Client,
    body: DownloadSDCardFileBody,
) -> DownloadSDCardFileResponse200 | ErrorResponse | None:
    """Download SD card file

     Download a specific file from the SD card to PC.

    **Requirements:**
    - Camera must be connected in `remote-transfer` or `contents-transfer` mode
    - Use content_id and file_id from the file list endpoint

    Args:
        camera_id (str):
        slot (DownloadSDCardFileSlot):
        content_id (int):
        file_id (int):
        body (DownloadSDCardFileBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DownloadSDCardFileResponse200 | ErrorResponse
    """

    return sync_detailed(
        camera_id=camera_id,
        slot=slot,
        content_id=content_id,
        file_id=file_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    camera_id: str,
    slot: DownloadSDCardFileSlot,
    content_id: int,
    file_id: int,
    *,
    client: AuthenticatedClient | Client,
    body: DownloadSDCardFileBody,
) -> Response[DownloadSDCardFileResponse200 | ErrorResponse]:
    """Download SD card file

     Download a specific file from the SD card to PC.

    **Requirements:**
    - Camera must be connected in `remote-transfer` or `contents-transfer` mode
    - Use content_id and file_id from the file list endpoint

    Args:
        camera_id (str):
        slot (DownloadSDCardFileSlot):
        content_id (int):
        file_id (int):
        body (DownloadSDCardFileBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DownloadSDCardFileResponse200 | ErrorResponse]
    """

    kwargs = _get_kwargs(
        camera_id=camera_id,
        slot=slot,
        content_id=content_id,
        file_id=file_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    camera_id: str,
    slot: DownloadSDCardFileSlot,
    content_id: int,
    file_id: int,
    *,
    client: AuthenticatedClient | Client,
    body: DownloadSDCardFileBody,
) -> DownloadSDCardFileResponse200 | ErrorResponse | None:
    """Download SD card file

     Download a specific file from the SD card to PC.

    **Requirements:**
    - Camera must be connected in `remote-transfer` or `contents-transfer` mode
    - Use content_id and file_id from the file list endpoint

    Args:
        camera_id (str):
        slot (DownloadSDCardFileSlot):
        content_id (int):
        file_id (int):
        body (DownloadSDCardFileBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DownloadSDCardFileResponse200 | ErrorResponse
    """

    return (
        await asyncio_detailed(
            camera_id=camera_id,
            slot=slot,
            content_id=content_id,
            file_id=file_id,
            client=client,
            body=body,
        )
    ).parsed
