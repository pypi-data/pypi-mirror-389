from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.data_contract import DataContract
from ...models.get_data_contract_response_404 import GetDataContractResponse404
from ...types import Response


def _get_kwargs(
    contract_id: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/data-contracts/{contract_id}",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DataContract | GetDataContractResponse404 | None:
    if response.status_code == 200:
        response_200 = DataContract.from_dict(response.json())

        return response_200

    if response.status_code == 404:
        response_404 = GetDataContractResponse404.from_dict(response.json())

        return response_404

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[DataContract | GetDataContractResponse404]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    contract_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[DataContract | GetDataContractResponse404]:
    """Get Data Contract

     Get a data contract by ID.

    Args:
        contract_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DataContract | GetDataContractResponse404]
    """

    kwargs = _get_kwargs(
        contract_id=contract_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    contract_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> DataContract | GetDataContractResponse404 | None:
    """Get Data Contract

     Get a data contract by ID.

    Args:
        contract_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DataContract | GetDataContractResponse404
    """

    return sync_detailed(
        contract_id=contract_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    contract_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[DataContract | GetDataContractResponse404]:
    """Get Data Contract

     Get a data contract by ID.

    Args:
        contract_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DataContract | GetDataContractResponse404]
    """

    kwargs = _get_kwargs(
        contract_id=contract_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    contract_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> DataContract | GetDataContractResponse404 | None:
    """Get Data Contract

     Get a data contract by ID.

    Args:
        contract_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DataContract | GetDataContractResponse404
    """

    return (
        await asyncio_detailed(
            contract_id=contract_id,
            client=client,
        )
    ).parsed
