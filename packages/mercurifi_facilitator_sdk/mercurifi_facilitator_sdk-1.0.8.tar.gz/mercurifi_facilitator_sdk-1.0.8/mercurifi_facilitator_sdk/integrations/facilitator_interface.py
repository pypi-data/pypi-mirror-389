from typing import Dict, Any
from enum import Enum, auto


class FacilitatorResponse(Dict[str, Any]):
    """
    Generic response wrapper for the X402 Facilitator API.

    This type is returned by most Facilitator SDK methods such as
    `get_supported`, `verify_payment`, and `settle_payment`.

    It is a dictionary-based container compatible with JSON responses
    from the Facilitator service.

    Examples
    --------
    >>> response = FacilitatorResponse({"isValid": True, "network": "base"})
    >>> response["isValid"]
    True
    """
    pass


class NetworkFamily(Enum):
    """
    Supported blockchain network families.

    Represents the two main categories of blockchains supported by
    the X402 Facilitator SDK — EVM-based and Solana-based networks.

    Attributes
    ----------
    EVM : NetworkFamily
        Ethereum Virtual Machine (EVM) family (e.g., Base, Ethereum, Polygon).
    SOLANA : NetworkFamily
        Solana family (e.g., Solana mainnet or devnet).

    Examples
    --------
    >>> NetworkFamily.EVM.name
    'EVM'
    """
    EVM = auto()
    SOLANA = auto()


class EvmNetwork(str, Enum):
    """
    Supported EVM-compatible networks.

    Maps logical network identifiers to canonical X402 values.

    Attributes
    ----------
    BASE : str
        Base Mainnet network.
    BASE_SEPOLIA : str
        Base Sepolia Testnet network.

    Examples
    --------
    >>> EvmNetwork.BASE.value
    'base'
    """
    BASE = "base"
    BASE_SEPOLIA = "base-sepolia"


class SolanaNetwork(str, Enum):
    """
    Supported Solana networks.

    Attributes
    ----------
    SOLANA_DEVNET : str
        Solana development network (test environment).
    SOLANA_MAINNET : str
        Solana main production network.

    Examples
    --------
    >>> SolanaNetwork.SOLANA_DEVNET.value
    'solana-devnet'
    """
    SOLANA_DEVNET = "solana-devnet"
    SOLANA_MAINNET = "solana-mainnet"


class EvmUSDCContract(str, Enum):
    """
    Canonical USDC token contract addresses for EVM networks.

    Attributes
    ----------
    BASE : str
        USDC contract address on Base Mainnet.
    BASE_SEPOLIA : str
        USDC contract address on Base Sepolia Testnet.

    Examples
    --------
    >>> EvmUSDCContract.BASE.value
    '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913'
    """
    BASE = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
    BASE_SEPOLIA = "0x036cbd53842c5426634e7929541ec2318f3dcf7e"


class SolanaUSDCContract(str, Enum):
    """
    Canonical USDC mint addresses for Solana networks.

    Attributes
    ----------
    SOLANA_DEVNET : str
        USDC mint address on Solana Devnet.
    SOLANA_MAINNET : str
        USDC mint address on Solana Mainnet.

    Examples
    --------
    >>> SolanaUSDCContract.SOLANA_MAINNET.value
    'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'
    """
    SOLANA_DEVNET = "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU"
    SOLANA_MAINNET = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
