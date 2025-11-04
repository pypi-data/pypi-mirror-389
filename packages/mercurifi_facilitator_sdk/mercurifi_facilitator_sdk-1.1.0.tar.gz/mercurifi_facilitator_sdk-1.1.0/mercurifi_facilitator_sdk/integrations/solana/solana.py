import json
import time
import base64
import base58
import secrets
import nacl.signing
from typing import Optional
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.message import MessageV0
from solders.transaction import VersionedTransaction
from solana.rpc.api import Client
from spl.token.instructions import (
    get_associated_token_address,
    approve_checked,
    ApproveCheckedParams,
)
from spl.token.constants import TOKEN_PROGRAM_ID


def generate_solana_payment_header(
    *,
    keypair: Keypair,
    to: str,
    value: str,
    asset: Optional[str],
    network: str,
    rpc_url: str,
    facilitator_address: str,
    valid_after: Optional[int] = None,
    valid_before: Optional[int] = None,
) -> str:
    """
    Generate and pre-approve a Solana X402 payment header using a VersionedTransaction (v0).

    This function prepares an **ApproveChecked** delegate authorization for the given
    facilitator address, signs the transaction with the provided keypair, and constructs
    a signed X402 header object ready for verification or settlement.

    The function is fully network-agnostic — all configuration values
    (e.g., `rpc_url`, `facilitator_address`) are injected by the `Facilitator` instance.

    Parameters
    ----------
    keypair : solders.keypair.Keypair
        Solana keypair used to sign the SPL-token authorization.
    to : str
        Recipient public key (Solana address).
    value : str
        Token amount to approve, expressed as a string (e.g., `"1.0"` for 1 USDC).
    asset : str, optional
        SPL-token mint address (e.g., USDC). Required.
    network : str
        Solana network identifier (e.g., `"solana-devnet"`).
    rpc_url : str
        RPC endpoint URL used for connection and transaction submission.
    facilitator_address : str
        Delegate address authorized to settle the approved amount.
    valid_after : int, optional
        UNIX timestamp (seconds) when the payment becomes valid.
        Defaults to the current timestamp.
    valid_before : int, optional
        UNIX timestamp (seconds) when the payment expires.
        Defaults to 5 minutes (300 seconds) after the current time.

    Returns
    -------
    str
        Base64-encoded JSON string representing the signed Solana X402 payment header.

    Raises
    ------
    RuntimeError
        If the VersionedTransaction fails to send or confirm on-chain.
    Exception
        If there is an unexpected network or signing error.

    Examples
    --------
    >>> from solders.keypair import Keypair
    >>> kp = Keypair()
    >>> header = generate_solana_payment_header(
    ...     keypair=kp,
    ...     to="RecipientPublicKey",
    ...     value="1.0",
    ...     asset="4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU",
    ...     network="solana-devnet",
    ...     rpc_url="https://api.devnet.solana.com",
    ...     facilitator_address="FacilitatorDelegatePublicKey",
    ... )
    >>> print(header[:50])
    eyJ4NDAyVmVyc2lvbiI6MSwic2NoZW1lIjoiZXhhY3Qi...
    """
    # Setup 
    connection = Client(rpc_url)
    sender = keypair.pubkey()
    facilitator = Pubkey.from_string(facilitator_address)
    mint = Pubkey.from_string(asset)

    # Associated Token Account (ATA)
    from_ata = get_associated_token_address(owner=sender, mint=mint)

    # ApproveChecked Instruction
    decimals = 6
    approve_amount = int(float(value) * (10**decimals))
    approve_ix = approve_checked(
        ApproveCheckedParams(
            program_id=TOKEN_PROGRAM_ID,
            source=from_ata,
            mint=mint,
            delegate=facilitator,
            owner=sender,
            amount=approve_amount,
            decimals=decimals,
            signers=[],
        )
    )

    # Get latest blockhash
    latest_blockhash = connection.get_latest_blockhash().value.blockhash

    # Build VersionedTransaction
    msg_v0 = MessageV0.try_compile(
        payer=sender,
        instructions=[approve_ix],
        address_lookup_table_accounts=[],
        recent_blockhash=latest_blockhash,
    )
    versioned_tx = VersionedTransaction(msg_v0, [keypair])

    # Send + confirm transaction
    try:
        sig = connection.send_transaction(versioned_tx)
        connection.confirm_transaction(sig.value, commitment="confirmed")
    except Exception as e:
        raise RuntimeError(f"Failed to send VersionedTransaction: {e}")

    # Validity window + nonce
    now = int(time.time())
    computed_valid_after = valid_after or now
    computed_valid_before = valid_before or (now + 300)
    nonce = "0x" + secrets.token_hex(32)

    # Build signed payload
    msg = {
        "x402Version": 1,
        "scheme": "exact",
        "network": network,
        "payload": {
            "from": str(sender),
            "to": to,
            "asset": asset,
            "value": value,
            "validAfter": computed_valid_after,
            "validBefore": computed_valid_before,
            "nonce": nonce,
        },
    }

    encoded_msg = json.dumps(msg, separators=(",", ":")).encode("utf-8")
    signing_key = nacl.signing.SigningKey(
        keypair.secret()[:32], encoder=nacl.encoding.RawEncoder
    )
    signature = signing_key.sign(encoded_msg).signature
    encoded_sig = base58.b58encode(signature).decode("utf-8")

    header = {**msg, "payload": {**msg["payload"], "signature": encoded_sig}}
    return base64.b64encode(json.dumps(header).encode("utf-8")).decode("utf-8")
