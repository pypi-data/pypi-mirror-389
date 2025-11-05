from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.api_response import ApiResponse
from ...models.error_response import ErrorResponse
from ...models.execute_action_body import ExecuteActionBody
from ...types import Response


def _get_kwargs(
    camera_id: str,
    action_name: str,
    *,
    body: ExecuteActionBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/api/cameras/{camera_id}/actions/{action_name}",
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
    action_name: str,
    *,
    client: AuthenticatedClient | Client,
    body: ExecuteActionBody,
) -> Response[ApiResponse | ErrorResponse]:
    r"""Execute camera action

     Execute a camera action such as shutter release, focus, or zoom control.

    ## Supported Actions

    ### shutter
    - Default (no params): Full shutter press (Down → wait 500ms → Up)
    - `{\"action\":\"down\"}`: Press and hold shutter (for continuous shooting)
    - `{\"action\":\"up\"}`: Release shutter (stop continuous shooting)

    ### half-press
    Half-press shutter for focus lock (S1 property)

    ### af-shutter
    Auto-focus then capture in one operation

    ### zoom
    Control zoom on power zoom lenses. Requires `{\"speed\": -10 to +10}` parameter.
    - Negative values: Zoom out (wide)
    - Positive values: Zoom in (tele)
    - Zero: Stop zoom

    Args:
        camera_id (str):
        action_name (str):
        body (ExecuteActionBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiResponse | ErrorResponse]
    """

    kwargs = _get_kwargs(
        camera_id=camera_id,
        action_name=action_name,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    camera_id: str,
    action_name: str,
    *,
    client: AuthenticatedClient | Client,
    body: ExecuteActionBody,
) -> ApiResponse | ErrorResponse | None:
    r"""Execute camera action

     Execute a camera action such as shutter release, focus, or zoom control.

    ## Supported Actions

    ### shutter
    - Default (no params): Full shutter press (Down → wait 500ms → Up)
    - `{\"action\":\"down\"}`: Press and hold shutter (for continuous shooting)
    - `{\"action\":\"up\"}`: Release shutter (stop continuous shooting)

    ### half-press
    Half-press shutter for focus lock (S1 property)

    ### af-shutter
    Auto-focus then capture in one operation

    ### zoom
    Control zoom on power zoom lenses. Requires `{\"speed\": -10 to +10}` parameter.
    - Negative values: Zoom out (wide)
    - Positive values: Zoom in (tele)
    - Zero: Stop zoom

    Args:
        camera_id (str):
        action_name (str):
        body (ExecuteActionBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiResponse | ErrorResponse
    """

    return sync_detailed(
        camera_id=camera_id,
        action_name=action_name,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    camera_id: str,
    action_name: str,
    *,
    client: AuthenticatedClient | Client,
    body: ExecuteActionBody,
) -> Response[ApiResponse | ErrorResponse]:
    r"""Execute camera action

     Execute a camera action such as shutter release, focus, or zoom control.

    ## Supported Actions

    ### shutter
    - Default (no params): Full shutter press (Down → wait 500ms → Up)
    - `{\"action\":\"down\"}`: Press and hold shutter (for continuous shooting)
    - `{\"action\":\"up\"}`: Release shutter (stop continuous shooting)

    ### half-press
    Half-press shutter for focus lock (S1 property)

    ### af-shutter
    Auto-focus then capture in one operation

    ### zoom
    Control zoom on power zoom lenses. Requires `{\"speed\": -10 to +10}` parameter.
    - Negative values: Zoom out (wide)
    - Positive values: Zoom in (tele)
    - Zero: Stop zoom

    Args:
        camera_id (str):
        action_name (str):
        body (ExecuteActionBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiResponse | ErrorResponse]
    """

    kwargs = _get_kwargs(
        camera_id=camera_id,
        action_name=action_name,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    camera_id: str,
    action_name: str,
    *,
    client: AuthenticatedClient | Client,
    body: ExecuteActionBody,
) -> ApiResponse | ErrorResponse | None:
    r"""Execute camera action

     Execute a camera action such as shutter release, focus, or zoom control.

    ## Supported Actions

    ### shutter
    - Default (no params): Full shutter press (Down → wait 500ms → Up)
    - `{\"action\":\"down\"}`: Press and hold shutter (for continuous shooting)
    - `{\"action\":\"up\"}`: Release shutter (stop continuous shooting)

    ### half-press
    Half-press shutter for focus lock (S1 property)

    ### af-shutter
    Auto-focus then capture in one operation

    ### zoom
    Control zoom on power zoom lenses. Requires `{\"speed\": -10 to +10}` parameter.
    - Negative values: Zoom out (wide)
    - Positive values: Zoom in (tele)
    - Zero: Stop zoom

    Args:
        camera_id (str):
        action_name (str):
        body (ExecuteActionBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiResponse | ErrorResponse
    """

    return (
        await asyncio_detailed(
            camera_id=camera_id,
            action_name=action_name,
            client=client,
            body=body,
        )
    ).parsed
