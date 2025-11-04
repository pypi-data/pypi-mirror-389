import json
import base64
import secrets
import time
from eth_account import Account
from eth_utils import keccak, to_hex
from eth_abi import encode as abi_encode
from eth_keys import keys


def generate_evm_payment_header(
    *,
    signer: Account,
    to: str,
    value: str,
    asset: str,
    network: str,
    valid_after: int | None = None,
    valid_before: int | None = None,
) -> str:
    """
    Generate an EIP-3009 (`transferWithAuthorization`) X402 payment header.

    This function creates a signed X402 header payload for **EVM-based networks**
    (e.g., Base or Base-Sepolia) following the EIP-3009 standard.
    It mirrors the behavior of:
    `ethers.Wallet.signTypedData(domain, types, message)` in JavaScript.

    Parameters
    ----------
    signer : eth_account.Account
        The EVM account object (private key) used for signing the authorization.
    to : str
        Recipient address for the transfer.
    value : str
        Payment amount as a decimal string (e.g., `"1.0"` for 1 USDC).
    asset : str
        ERC-20 token contract address (e.g., USDC contract).
    network : str
        Network name (e.g., `"base"` or `"base-sepolia"`).
    valid_after : int, optional
        UNIX timestamp when the authorization becomes valid.
        Defaults to 10 seconds before the current time.
    valid_before : int, optional
        UNIX timestamp when the authorization expires.
        Defaults to 1 hour after the current time.

    Returns
    -------
    str
        Base64-encoded JSON string representing the signed X402 EIP-3009 header.

    Raises
    ------
    ValueError
        If any signing or encoding step fails unexpectedly.
    Exception
        For lower-level cryptographic or network-related errors.

    Notes
    -----
    - The function automatically computes the correct `chainId` for Base mainnet and Base-Sepolia.
    - The generated header can be verified or settled using the Facilitator API.
    - The USDC domain follows the official EIP-3009 schema with `"USD Coin"` as name and `"2"` as version.

    Examples
    --------
    >>> from eth_account import Account
    >>> signer = Account.from_key("0x0123...abcd")
    >>> header = generate_evm_payment_header(
    ...     signer=signer,
    ...     to="0xRecipientAddress",
    ...     value="1.0",
    ...     asset="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    ...     network="base"
    ... )
    >>> print(header[:60])
    eyJ4NDAyVmVyc2lvbiI6MSwic2NoZW1lIjoiZXhhY3QiLCJuZXR3b3JrIjoiYmFzZSIs...
    """

    # Setup validity window + nonce
    now = int(time.time())
    computed_valid_after = valid_after or now
    computed_valid_before = valid_before or (now + 300)
    nonce = "0x" + secrets.token_hex(32)

    # EIP-712 Domain (must match backend)
    chain_id = 8453 if "base" in network and "base-sepolia" not in network else 84532
    domain = {
        "name": "USD Coin",
        "version": "2",
        "chainId": chain_id,
        "verifyingContract": asset,
    }

    # Typehash constants
    typehash = keccak(
        b"TransferWithAuthorization(address from,address to,uint256 value,uint256 validAfter,uint256 validBefore,bytes32 nonce)"
    )
    domain_typehash = keccak(
        b"EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"
    )

    # Message encoding
    from_addr = signer.address
    parsed_value = int(float(value) * 1e6)

    struct_hash = keccak(
        abi_encode(
            [
                "bytes32",
                "address",
                "address",
                "uint256",
                "uint256",
                "uint256",
                "bytes32",
            ],
            [
                typehash,
                from_addr,
                to,
                parsed_value,
                valid_after,
                valid_before,
                bytes.fromhex(nonce.replace("0x", "")),
            ],
        )
    )

    # Domain separator
    domain_hash = keccak(
        abi_encode(
            [
                "bytes32",
                "bytes32",
                "bytes32",
                "uint256",
                "address",
            ],
            [
                domain_typehash,
                keccak(text=domain["name"]),
                keccak(text=domain["version"]),
                domain["chainId"],
                domain["verifyingContract"],
            ],
        )
    )

    # EIP-191 digest
    digest = keccak(b"\x19\x01" + domain_hash + struct_hash)

    # Sign the digest
    priv_bytes = bytes.fromhex(signer.key.hex().replace("0x", ""))
    priv_key = keys.PrivateKey(priv_bytes)
    signed = priv_key.sign_msg_hash(digest)

    # Normalize v to 27/28 for ethers compatibility
    v = signed.v
    if v in (0, 1):
        v += 27

    # Combine r || s || v
    signature_bytes = (
        signed.r.to_bytes(32, "big")
        + signed.s.to_bytes(32, "big")
        + bytes([v])
    )
    signature_hex = "0x" + signature_bytes.hex()

    print("Digest:", to_hex(digest))
    print("Signature:", signature_hex)

    # Build final X402 header
    header = {
        "x402Version": 1,
        "scheme": "exact",
        "network": network,
        "payload": {
            "from": from_addr,
            "to": to,
            "value": str(parsed_value),
            "validAfter": computed_valid_after,
            "validBefore": computed_valid_before,
            "nonce": nonce,
            "asset": asset,
            "signature": signature_hex,
        },
    }

    return base64.b64encode(json.dumps(header).encode()).decode()
