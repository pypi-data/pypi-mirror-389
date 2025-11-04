from typing import Optional, Dict, Any
from mercurifi_facilitator_sdk.integrations.facilitator_interface import NetworkFamily
from mercurifi_facilitator_sdk.integrations.facilitator_registry import NETWORK_REGISTRY
from .integrations.facilitator_api import get_supported, verify_payment, settle_payment


class Facilitator:
    """
    X402 Facilitator SDK Client (Python Edition).

    A lightweight Python client for the Mercuri X402 Facilitator API, providing
    a unified interface to generate, verify, and settle X402-compliant payments
    across EVM and Solana networks.

    This class mirrors the Node.js `Facilitator` implementation for parity between SDKs.

    Parameters
    ----------
    network : str
        Target blockchain network key (e.g., `'base'`, `'solana-devnet'`).
    base_url : str, optional
        Facilitator API base URL. Defaults to ``"https://facilitator.mercuri.finance"``.

    Raises
    ------
    ValueError
        If the provided network is not supported or missing from the registry.

    Examples
    --------
    >>> from facilitator_sdk import Facilitator
    >>> facilitator = Facilitator(network="base")
    >>> supported = facilitator.get_supported()
    >>> print(supported)
    """
    def __init__(
        self,
        network: str,
        base_url: str = "https://facilitator.mercuri.finance",
    ):
        self.base_url = base_url
        self.network = network

        config = NETWORK_REGISTRY.get(network)
        if not config:
            raise ValueError(f"Unsupported network: {network}")

        self.family: NetworkFamily = config["family"]
        self.default_asset: str = config["default_asset"]
        self.header_generator = config["header_generator"]
        self.rpc_url: str = config["rpc_url"]
        self.facilitator_delegate: Optional[str] = config.get("facilitator_delegate")


    def get_supported(self) -> Dict[str, Any]:
        """
        Retrieve supported networks and configurations from the Facilitator API.

        Returns
        -------
        dict
            A JSON-compatible dictionary containing supported payment kinds and network info.

        Examples
        --------
        >>> facilitator.get_supported()
        {'kinds': [{'x402Version': 1, 'scheme': 'exact', 'network': 'base'}]}
        """
        return get_supported(self.base_url)


    def verify_payment(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify a payment request against the Facilitator API.

        Parameters
        ----------
        request : dict
            The verification payload containing the signed payment header and requirements.

        Returns
        -------
        dict
            API response indicating whether the payment header is valid.

        Raises
        ------
        Exception
            If the verification request fails or returns a non-OK status.

        Examples
        --------
        >>> facilitator.verify_payment({
        ...     "x402Version": 1,
        ...     "paymentHeader": "eyJ...base64...",
        ...     "paymentRequirements": {"scheme": "exact", "network": "base"}
        ... })
        {'isValid': True, 'invalidReason': None}
        """
        return verify_payment(self.base_url, request)


    def settle_payment(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Settle a verified payment via the Facilitator API.

        Parameters
        ----------
        request : dict
            The settlement payload containing the verified header and requirements.

        Returns
        -------
        dict
            API response confirming settlement success and transaction metadata.

        Examples
        --------
        >>> facilitator.settle_payment({
        ...     "x402Version": 1,
        ...     "paymentHeader": "eyJ...base64...",
        ...     "paymentRequirements": {"scheme": "exact", "network": "solana-devnet"}
        ... })
        {'event': 'payment.settled', 'txHash': 'abc123...'}
        """
        return settle_payment(self.base_url, request)


    def generate_payment_header(
        self,
        *,
        to: str,
        value: str,
        signer=None,
        solana_keypair=None,
        asset: Optional[str] = None,
        valid_after: Optional[int] = None,
        valid_before: Optional[int] = None,
    ) -> str:
        """
        Generate a signed X402 payment header for the configured network.

        For EVM networks, this creates an **EIP-712 TransferWithAuthorization**
        signature. For Solana networks, this performs an **ApproveChecked**
        delegate authorization with an Ed25519 signature.

        Parameters
        ----------
        to : str
            Recipient wallet address (EVM or Solana public key).
        value : str
            Payment amount (in token units, e.g., `'1.00'`).
        signer : Optional[object]
            EVM-compatible signer (e.g., ``eth_account.Account`` or Web3 wallet).
        solana_keypair : Optional[object]
            Solana ``Keypair`` used to sign SPL-token authorizations.
        asset : str, optional
            Token contract (EVM) or mint (Solana). Defaults to network’s ``default_asset``.
        valid_after : int, optional
            Timestamp (seconds) when the payment becomes valid.
        valid_before : int, optional
            Timestamp (seconds) when the payment expires.

        Returns
        -------
        str
            Base64-encoded JSON string representing the signed payment header.

        Raises
        ------
        ValueError
            If the required signer or keypair is missing for the selected network.

        Examples
        --------
        >>> facilitator.generate_payment_header(
        ...     to="0xRecipientAddress",
        ...     value="1.0",
        ...     signer=wallet,
        ... )
        'eyJ4NDAyVmVyc2lvbiI6IDEsICJwYXlsb2FkIjog...'
        """
        if self.family == NetworkFamily.EVM:
            if not signer:
                raise ValueError("EVM signer required for EVM networks")
            return self.header_generator(
                signer=signer,
                to=to,
                value=value,
                asset=asset or self.default_asset,
                network=self.network,
                valid_after=valid_after,
                valid_before=valid_before,
            )

        elif self.family == NetworkFamily.SOLANA:
            if not solana_keypair:
                raise ValueError("Solana keypair required for Solana networks")
            return self.header_generator(
                keypair=solana_keypair,
                to=to,
                value=value,
                asset=asset or self.default_asset,
                network=self.network,
                rpc_url=self.rpc_url,
                facilitator_address=self.facilitator_delegate,
                valid_after=valid_after,
                valid_before=valid_before,
            )

        else:
            raise ValueError(f"Unsupported network family: {self.family}")


    def generate_payment_requirements(
        self,
        *,
        pay_to: str,
        asset: Optional[str] = None,
        description: str = "X402 payment request",
        max_amount_required: str = "1.00",
        mime_type: str = "application/json",
        max_timeout_seconds: int = 300,
        resource: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
        output_schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Construct an X402-compliant payment requirements object.

        Parameters
        ----------
        pay_to : str
            Recipient wallet address.
        asset : str, optional
            Token contract or mint address. Defaults to ``default_asset`` for the network.
        description : str, optional
            Description of the payment. Defaults to ``"X402 payment request"``.
        max_amount_required : str, optional
            Maximum payment amount (default: ``"1.00"``).
        mime_type : str, optional
            MIME type of the request (default: ``"application/json"``).
        max_timeout_seconds : int, optional
            Time in seconds before request expires (default: 300).
        resource : str, optional
            Optional resource identifier.
        extra : dict, optional
            Arbitrary metadata fields.
        output_schema : dict, optional
            Optional output schema specification.

        Returns
        -------
        dict
            The complete X402 payment requirements structure.

        Examples
        --------
        >>> facilitator.generate_payment_requirements(
        ...     pay_to="0xRecipient",
        ...     description="Subscription payment",
        ...     max_amount_required="10.00"
        ... )
        {'scheme': 'exact', 'network': 'base', 'payTo': '0xRecipient', ...}
        """
        data = {
            "scheme": "exact",
            "network": self.network,
            "payTo": pay_to,
            "asset": asset or self.default_asset,
            "description": description,
            "mimeType": mime_type,
            "maxAmountRequired": max_amount_required,
            "maxTimeoutSeconds": max_timeout_seconds,
        }

        if resource:
            data["resource"] = resource
        if extra:
            data["extra"] = extra
        if output_schema:
            data["outputSchema"] = output_schema

        return data
