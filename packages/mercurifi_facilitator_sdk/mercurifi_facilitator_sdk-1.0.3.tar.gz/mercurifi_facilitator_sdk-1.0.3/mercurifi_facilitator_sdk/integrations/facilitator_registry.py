from .facilitator_interface import (
    NetworkFamily,
    EvmNetwork,
    SolanaNetwork,
    EvmUSDCContract,
    SolanaUSDCContract,
)
from .evm.evm import generate_evm_payment_header
from .solana.solana import generate_solana_payment_header


NETWORK_REGISTRY = {
    EvmNetwork.BASE.value: {
        "family": NetworkFamily.EVM,
        "default_asset": EvmUSDCContract.BASE.value,
        "header_generator": generate_evm_payment_header,
        "rpc_url": "https://mainnet.base.org",
    },
    EvmNetwork.BASE_SEPOLIA.value: {
        "family": NetworkFamily.EVM,
        "default_asset": EvmUSDCContract.BASE_SEPOLIA.value,
        "header_generator": generate_evm_payment_header,
        "rpc_url": "https://sepolia.base.org",
    },
    SolanaNetwork.SOLANA_DEVNET.value: {
        "family": NetworkFamily.SOLANA,
        "default_asset": SolanaUSDCContract.SOLANA_DEVNET.value,
        "header_generator": generate_solana_payment_header,
        "rpc_url": "https://api.devnet.solana.com",
        "facilitator_delegate": "2kQPdFFffYhskzSKX9uBYuDSWEuSphgJrVmcrofvVnMk",
    },
    SolanaNetwork.SOLANA_MAINNET.value: {
        "family": NetworkFamily.SOLANA,
        "default_asset": SolanaUSDCContract.SOLANA_MAINNET.value,
        "header_generator": generate_solana_payment_header,
        "rpc_url": "https://api.mainnet-beta.solana.com",
        "facilitator_delegate": "2kQPdFFffYhskzSKX9uBYuDSWEuSphgJrVmcrofvVnMk",  
    },
}
