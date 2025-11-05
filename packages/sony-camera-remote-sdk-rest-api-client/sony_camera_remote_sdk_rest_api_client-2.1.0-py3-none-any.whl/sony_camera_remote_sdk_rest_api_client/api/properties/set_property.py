from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error_response import ErrorResponse
from ...models.property_response import PropertyResponse
from ...models.set_property_body import SetPropertyBody
from ...types import Response


def _get_kwargs(
    camera_id: str,
    property_name: str,
    *,
    body: SetPropertyBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": f"/api/cameras/{camera_id}/properties/{property_name}",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | PropertyResponse | None:
    if response.status_code == 200:
        response_200 = PropertyResponse.from_dict(response.json())

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
    body: SetPropertyBody,
) -> Response[ErrorResponse | PropertyResponse]:
    r"""Set property value

     Set a camera property to a new value.

    Values can be specified in multiple formats:
    - **Hex**: \"0xC80\", \"0x0002\"
    - **Decimal**: \"3200\", 3200, \"2\", 2
    - **SDK enum**: \"CrISO_3200\", \"CrFocus_AF_S\"
    - **Friendly names**: \"f/5.6\", \"1/250\", \"wide\", \"center\" (where supported)

    The API automatically parses and converts values to the correct SDK format.

    See API_DOCUMENTATION.md for property-specific enum values and examples.

    Args:
        camera_id (str):
        property_name (str):
        body (SetPropertyBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorResponse | PropertyResponse]
    """

    kwargs = _get_kwargs(
        camera_id=camera_id,
        property_name=property_name,
        body=body,
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
    body: SetPropertyBody,
) -> ErrorResponse | PropertyResponse | None:
    r"""Set property value

     Set a camera property to a new value.

    Values can be specified in multiple formats:
    - **Hex**: \"0xC80\", \"0x0002\"
    - **Decimal**: \"3200\", 3200, \"2\", 2
    - **SDK enum**: \"CrISO_3200\", \"CrFocus_AF_S\"
    - **Friendly names**: \"f/5.6\", \"1/250\", \"wide\", \"center\" (where supported)

    The API automatically parses and converts values to the correct SDK format.

    See API_DOCUMENTATION.md for property-specific enum values and examples.

    Args:
        camera_id (str):
        property_name (str):
        body (SetPropertyBody):

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
        body=body,
    ).parsed


async def asyncio_detailed(
    camera_id: str,
    property_name: str,
    *,
    client: AuthenticatedClient | Client,
    body: SetPropertyBody,
) -> Response[ErrorResponse | PropertyResponse]:
    r"""Set property value

     Set a camera property to a new value.

    Values can be specified in multiple formats:
    - **Hex**: \"0xC80\", \"0x0002\"
    - **Decimal**: \"3200\", 3200, \"2\", 2
    - **SDK enum**: \"CrISO_3200\", \"CrFocus_AF_S\"
    - **Friendly names**: \"f/5.6\", \"1/250\", \"wide\", \"center\" (where supported)

    The API automatically parses and converts values to the correct SDK format.

    See API_DOCUMENTATION.md for property-specific enum values and examples.

    Args:
        camera_id (str):
        property_name (str):
        body (SetPropertyBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorResponse | PropertyResponse]
    """

    kwargs = _get_kwargs(
        camera_id=camera_id,
        property_name=property_name,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    camera_id: str,
    property_name: str,
    *,
    client: AuthenticatedClient | Client,
    body: SetPropertyBody,
) -> ErrorResponse | PropertyResponse | None:
    r"""Set property value

     Set a camera property to a new value.

    Values can be specified in multiple formats:
    - **Hex**: \"0xC80\", \"0x0002\"
    - **Decimal**: \"3200\", 3200, \"2\", 2
    - **SDK enum**: \"CrISO_3200\", \"CrFocus_AF_S\"
    - **Friendly names**: \"f/5.6\", \"1/250\", \"wide\", \"center\" (where supported)

    The API automatically parses and converts values to the correct SDK format.

    See API_DOCUMENTATION.md for property-specific enum values and examples.

    Args:
        camera_id (str):
        property_name (str):
        body (SetPropertyBody):

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
            body=body,
        )
    ).parsed
