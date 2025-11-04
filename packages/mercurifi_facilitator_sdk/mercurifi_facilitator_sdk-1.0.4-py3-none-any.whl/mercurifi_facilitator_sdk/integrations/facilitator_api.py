import requests
from typing import Dict, Any

HEADERS = {"Content-Type": "application/json", "X402-Version": "1"}


def get_supported(base_url: str) -> Dict[str, Any]:
    """
    Retrieve the list of supported networks and payment schemes from the Facilitator API.

    Parameters
    ----------
    base_url : str
        Base URL of the Facilitator API (e.g., ``"https://facilitator.mercuri.finance"``).

    Returns
    -------
    dict
        JSON response containing supported network configurations and versions.

    Raises
    ------
    requests.HTTPError
        If the request fails or the API responds with a non-2xx status.

    Examples
    --------
    >>> get_supported("https://facilitator.mercuri.finance")
    {'kinds': [{'x402Version': 1, 'scheme': 'exact', 'network': 'base'}]}
    """
    res = requests.get(f"{base_url}/v2/x402/supported")
    res.raise_for_status()
    return res.json()


def verify_payment(base_url: str, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verify an X402 payment session with the Facilitator API.

    Parameters
    ----------
    base_url : str
        Base URL of the Facilitator API.
    body : dict
        Verification payload containing the `paymentHeader` and `paymentRequirements`.

    Returns
    -------
    dict
        Verification response indicating whether the payment header is valid.

    Raises
    ------
    requests.HTTPError
        If the request fails or the response status is not OK.

    Examples
    --------
    >>> payload = {
    ...     "x402Version": 1,
    ...     "paymentHeader": "eyJ...base64...",
    ...     "paymentRequirements": {"scheme": "exact", "network": "base"}
    ... }
    >>> verify_payment("https://facilitator.mercuri.finance", payload)
    {'isValid': True, 'invalidReason': None}
    """
    res = requests.post(f"{base_url}/v2/x402/verify", json=body, headers=HEADERS)
    res.raise_for_status()
    return res.json()


def settle_payment(base_url: str, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Settle a previously verified X402 payment via the Facilitator API.

    Parameters
    ----------
    base_url : str
        Base URL of the Facilitator API.
    body : dict
        Settlement payload containing the verified payment header and requirements.

    Returns
    -------
    dict
        Settlement confirmation, including transaction metadata (e.g., hash, timestamp).

    Raises
    ------
    requests.HTTPError
        If the request fails or returns a non-success status code.

    Examples
    --------
    >>> payload = {
    ...     "x402Version": 1,
    ...     "paymentHeader": "eyJ...base64...",
    ...     "paymentRequirements": {"scheme": "exact", "network": "solana-devnet"}
    ... }
    >>> settle_payment("https://facilitator.mercuri.finance", payload)
    {'event': 'payment.settled', 'txHash': '4Gf8H...abc'}
    """
    res = requests.post(f"{base_url}/v2/x402/settle", json=body, headers=HEADERS)
    res.raise_for_status()
    return res.json()
