# **Mercuri Finance**

## **`mercuri_facilitator_sdk`**

The **Mercuri Facilitator SDK (Python)** provides a unified interface for interacting with the **X402 Facilitator API**, including generation of payment headers, verification, settlement, and discovery of supported blockchain payment kinds.

![PyPI](https://img.shields.io/pypi/v/mercurifi_facilitator_sdk)
![Python](https://img.shields.io/pypi/pyversions/mercurifi_facilitator_sdk)
![License](https://img.shields.io/pypi/l/mercurifi_facilitator_sdk)

---

## **Features**

- **Generate X402 Payment Headers** for **EVM (EIP-3009)** and **Solana**
- **Verify Payment Sessions** before settlement
- **Settle Authorized Payments** via the Facilitator
- **List Supported Networks & Schemes**
- **Lightweight & Secure** — built on `requests`, `eth-account`, and `solana`

---

## **Installation**

```bash
pip install mercuri_facilitator_sdk
```

---

## **Usage**

### **1. Initialize the Facilitator Client**

```python
from mercuri_facilitator_sdk import Facilitator

facilitator = Facilitator(network="base", base_url="https://facilitator.mercuri.finance")
```

---

### **2. List Supported Payment Kinds**

```python
supported = facilitator.get_supported()
print(supported)
```

**Example Output**

```json
{
  "kinds": [
    { "x402Version": 1, "scheme": "exact", "network": "base" },
    { "x402Version": 1, "scheme": "exact", "network": "solana-devnet" }
  ]
}
```

---

### **3. Generate a Payment Header**

#### EVM Example (Base / Ethereum)

```python
from eth_account import Account
from mercuri_facilitator_sdk.integrations.evm_header import generate_evm_payment_header

signer = Account.from_key("0xYOUR_PRIVATE_KEY")

header = generate_evm_payment_header(
    signer=signer,
    to="0xRecipient...",
    value="1.00",
)

print(header)
```

#### Solana Example

```python
from solders.keypair import Keypair
from mercuri_facilitator_sdk.integrations.solana_header import generate_solana_payment_header

private_key_bytes = bytes(json.loads("0xYOUR_PRIVATE_KEY"))
sender = Keypair.from_bytes(private_key_bytes)

header = generate_solana_payment_header(
    keypair=sender,
    to="RecipientPublicKey...",
    value="1.00",
)

print(header)
```

---

### **4. Verify a Payment Session**

```python
verify_response = facilitator.verify_payment({
    "x402Version": 1,
    "paymentHeader": "eyJhbGciOi...",
    "paymentRequirements": {
        "scheme": "exact",
        "network": "base",
        "payTo": "0xRecipient...",
        "asset": "0xAsset...",
        "description": "Test transaction"
    }
})

print(verify_response)
```

**Example Response**

```json
{
  "isValid": true,
  "invalidReason": null
}
```

---

### **5. Settle a Verified Payment**

```python
settle_response = facilitator.settle_payment({
    "x402Version": 1,
    "paymentHeader": "eyJhbGciOi...",
    "paymentRequirements": {
        "scheme": "exact",
        "network": "base",
        "payTo": "0xRecipient...",
        "asset": "0xAsset..."
    }
})

print(settle_response)
```

**Example Response**

```json
{
  "x402Version": 1,
  "event": "payment.settled",
  "txHash": "0xTransactionHash...",
  "network": "base",
  "timestamp": "2025-11-03T09:00:32.280Z"
}
```

---

## **API Reference**

| Method                                        | Description                                                |
| --------------------------------------------- | ---------------------------------------------------------- |
| `Facilitator.get_supported()`                 | Lists supported payment kinds and networks.                |
| `Facilitator.verify_payment(request)`         | Verifies a payment header with the facilitator.            |
| `Facilitator.settle_payment(request)`         | Settles a verified payment session.                        |
| `Facilitator.generate_payment_header()`       | Creates a Base64-encoded payment header for EVM or Solana. |
| `Facilitator.generate_payment_requirements()` | Builds a valid `X402PaymentRequirements` payload.          |

---

### **Payment Header Fields**

| Field         | Type | Description                                      |
| ------------- | ---- | ------------------------------------------------ |
| `x402Version` | int  | Protocol version (1).                            |
| `scheme`      | str  | Payment scheme (e.g., `"exact"`).                |
| `network`     | str  | Blockchain network (EVM / Solana).               |
| `payload`     | dict | Contains all signed fields (from, to, value...). |

---

## **Error Handling**

| HTTP Code | Error                 | Description                          |
| --------- | --------------------- | ------------------------------------ |
| `400`     | Bad Request           | Check payload formatting.            |
| `404`     | Not Found             | Verify the facilitator endpoint URL. |
| `500`     | Internal Server Error | Retry or contact support.            |

---

## **Parity with Node SDK**

The Python SDK (`mercuri_facilitator_sdk`) mirrors the TypeScript SDK (`@mercuri/facilitator-sdk`) in:

- **Method names & signatures**
- **Header formats (EVM + Solana)**
- **Verification & settlement flow**

This ensures identical integration behavior across Node.js and Python environments.

---

## **License**

MIT © 2025 **Mercuri Finance**
