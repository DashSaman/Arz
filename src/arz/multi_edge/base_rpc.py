"""Bounded read-only Base RPC helpers for historical research.

This module deliberately exposes no transaction submission, signing, wallet or
state-changing method. Raw responses belong in ignored runtime storage.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import json
import math
import time
import urllib.parse
import urllib.request
from typing import Any, Callable

from .events import WalletEvent

BASE_RPC_URL = "https://mainnet.base.org"
BASE_RPC_HOST = "mainnet.base.org"
SWAP_TOPIC = "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"
_ALLOWED_METHODS = {
    "eth_blockNumber",
    "eth_getBlockByNumber",
    "eth_getLogs",
    "eth_getTransactionByHash",
    "eth_getTransactionReceipt",
    "eth_call",
}
_ADDRESS_HEX_LEN = 42


def _address(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != _ADDRESS_HEX_LEN or not value.startswith("0x"):
        raise ValueError(f"Invalid {name} address")
    try:
        int(value[2:], 16)
    except ValueError as exc:
        raise ValueError(f"Invalid {name} address") from exc
    return value.lower()


def _nonnegative_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")
    return value


@dataclass(frozen=True)
class PoolSpec:
    symbol: str
    pool: str
    base_token: str
    quote_token: str
    token0: str
    token1: str
    base_decimals: int
    quote_decimals: int
    fee_ppm: int

    def __post_init__(self) -> None:
        if not isinstance(self.symbol, str) or not self.symbol:
            raise ValueError("Invalid symbol")
        for name in ("pool", "base_token", "quote_token", "token0", "token1"):
            object.__setattr__(self, name, _address(getattr(self, name), name))
        if {self.token0, self.token1} != {self.base_token, self.quote_token}:
            raise ValueError("Pool token orientation mismatch")
        for name in ("base_decimals", "quote_decimals"):
            value = getattr(self, name)
            if type(value) is not int or not 0 <= value <= 36:
                raise ValueError(f"Invalid {name}")
        if type(self.fee_ppm) is not int or not 0 <= self.fee_ppm < 1_000_000:
            raise ValueError("Invalid pool fee")


WETH_USDC = PoolSpec(
    symbol="WETH/USDC",
    pool="0xd0b53d9277642d899df5c87a3966a349a798f224",
    base_token="0x4200000000000000000000000000000000000006",
    quote_token="0x833589fcd6edb6e08f4c7c32d4f71b54bda02913",
    token0="0x4200000000000000000000000000000000000006",
    token1="0x833589fcd6edb6e08f4c7c32d4f71b54bda02913",
    base_decimals=18,
    quote_decimals=6,
    fee_ppm=500,
)

CBBTC_USDC = PoolSpec(
    symbol="cbBTC/USDC",
    pool="0xfbb6eed8e7aa03b138556eedaf5d271a5e1e43ef",
    base_token="0xcbb7c0000ab88b473b1f5afd9ef808440eed33bf",
    quote_token="0x833589fcd6edb6e08f4c7c32d4f71b54bda02913",
    token0="0x833589fcd6edb6e08f4c7c32d4f71b54bda02913",
    token1="0xcbb7c0000ab88b473b1f5afd9ef808440eed33bf",
    base_decimals=8,
    quote_decimals=6,
    fee_ppm=500,
)


class _SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        parsed = urllib.parse.urlsplit(newurl)
        if parsed.scheme != "https" or parsed.hostname != BASE_RPC_HOST or parsed.port not in (None, 443):
            raise ValueError("RPC redirect outside fixed host")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _http_transport(payload: dict[str, Any], *, timeout: float = 15.0) -> dict[str, Any]:
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not 0 < timeout <= 30:
        raise ValueError("Invalid timeout")
    raw = json.dumps(payload, separators=(",", ":"), allow_nan=False).encode()
    request = urllib.request.Request(
        BASE_RPC_URL,
        data=raw,
        method="POST",
        headers={"Content-Type": "application/json", "User-Agent": "ArzResearch/0.1 read-only"},
    )
    opener = urllib.request.build_opener(_SafeRedirect)
    with opener.open(request, timeout=timeout) as response:
        body = response.read(2_000_001)
    if len(body) > 2_000_000:
        raise ValueError("Oversized RPC response")
    parsed = json.loads(body, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"Nonfinite JSON: {value}")))
    if not isinstance(parsed, dict):
        raise ValueError("Malformed RPC response")
    return parsed


def rpc_call(
    method: str,
    params: list[Any],
    *,
    transport: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
) -> Any:
    if method not in _ALLOWED_METHODS:
        raise ValueError("RPC method is not on the read-only allowlist")
    if not isinstance(params, list):
        raise ValueError("RPC params must be a list")
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    response = (transport or _http_transport)(payload)
    if not isinstance(response, dict):
        raise ValueError("Malformed RPC response")
    if "error" in response:
        raise ValueError(f"RPC error: {response['error']}")
    if "result" not in response:
        raise ValueError("Malformed RPC response")
    return response["result"]


def _hex_int(value: object, name: str) -> int:
    if not isinstance(value, str) or not value.startswith("0x"):
        raise ValueError(f"Invalid {name} hex")
    try:
        return int(value, 16)
    except ValueError as exc:
        raise ValueError(f"Invalid {name} hex") from exc


def _decode_address_word(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.startswith("0x") or len(value) != 66:
        raise ValueError(f"Invalid {name} return word")
    if int(value[2:26], 16) != 0:
        raise ValueError(f"Non-canonical {name} address word")
    return _address("0x" + value[-40:], name)


def verify_pool(spec: PoolSpec, *, rpc: Callable[[str, list[Any]], Any] = rpc_call) -> dict[str, Any]:
    calls = {
        "token0": "0x0dfe1681",
        "token1": "0xd21220a7",
        "fee": "0xddca3f43",
    }
    token0 = _decode_address_word(rpc("eth_call", [{"to": spec.pool, "data": calls["token0"]}, "latest"]), "token0")
    token1 = _decode_address_word(rpc("eth_call", [{"to": spec.pool, "data": calls["token1"]}, "latest"]), "token1")
    fee_raw = rpc("eth_call", [{"to": spec.pool, "data": calls["fee"]}, "latest"])
    fee = _hex_int(fee_raw, "fee")
    if token0 != spec.token0 or token1 != spec.token1:
        raise ValueError("Pool token identities do not match reviewed specification")
    if fee != spec.fee_ppm:
        raise ValueError("Pool fee does not match reviewed specification")
    return {"pool": spec.pool, "token0": token0, "token1": token1, "fee_ppm": fee}


def fetch_logs(
    spec: PoolSpec,
    from_block: int,
    to_block: int,
    *,
    rpc: Callable[[str, list[Any]], Any] = rpc_call,
    max_span: int = 5_000,
) -> list[dict[str, Any]]:
    start = _nonnegative_int(from_block, "from_block")
    end = _nonnegative_int(to_block, "to_block")
    if end < start:
        raise ValueError("Invalid block range")
    if type(max_span) is not int or max_span < 1:
        raise ValueError("Invalid max span")
    if end - start > max_span:
        raise ValueError("Block span exceeds bounded research limit")
    result = rpc("eth_getLogs", [{
        "address": spec.pool,
        "fromBlock": hex(start),
        "toBlock": hex(end),
        "topics": [SWAP_TOPIC],
    }])
    if not isinstance(result, list):
        raise ValueError("Malformed log result")
    return result


def _signed_word(word: str) -> int:
    value = int(word, 16)
    return value - (1 << 256) if value >= (1 << 255) else value


def _topic_address(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.startswith("0x") or len(value) != 66:
        raise ValueError(f"Invalid {name} topic")
    if int(value[2:26], 16) != 0:
        raise ValueError(f"Non-canonical {name} topic")
    return _address("0x" + value[-40:], name)


@dataclass(frozen=True)
class SwapObservation:
    event_id: str
    block_number: int
    tx_hash: str
    log_index: int
    pool: str
    symbol: str
    sender: str
    recipient: str
    side: str
    asset_amount: float
    quote_amount: float
    wallet: str | None = None
    network_fee_native: float | None = None
    ts: int | None = None


def decode_swap_log(log: dict[str, Any], spec: PoolSpec) -> SwapObservation:
    if not isinstance(log, dict):
        raise ValueError("Malformed swap log")
    if _address(log.get("address"), "log pool") != spec.pool:
        raise ValueError("Unexpected pool")
    topics = log.get("topics")
    if not isinstance(topics, list) or len(topics) != 3 or str(topics[0]).lower() != SWAP_TOPIC:
        raise ValueError("Unexpected swap topic")
    if log.get("removed") is True:
        raise ValueError("Removed log is not finalized evidence")
    data = log.get("data")
    if not isinstance(data, str) or not data.startswith("0x") or len(data) != 2 + 32 * 2 * 5:
        raise ValueError("Malformed swap data")
    words = [data[2 + index * 64:2 + (index + 1) * 64] for index in range(5)]
    amount0, amount1 = _signed_word(words[0]), _signed_word(words[1])
    if amount0 == 0 or amount1 == 0 or (amount0 > 0) == (amount1 > 0):
        raise ValueError("Swap amounts must have opposing nonzero signs")
    if spec.token0 == spec.base_token:
        base_raw, quote_raw = amount0, amount1
    else:
        base_raw, quote_raw = amount1, amount0
    if base_raw < 0 and quote_raw > 0:
        side = "buy"
    elif base_raw > 0 and quote_raw < 0:
        side = "sell"
    else:
        raise ValueError("Swap orientation does not match base/quote tokens")
    block = _hex_int(log.get("blockNumber"), "blockNumber")
    log_index = _hex_int(log.get("logIndex"), "logIndex")
    tx_hash = log.get("transactionHash")
    if not isinstance(tx_hash, str) or not tx_hash.startswith("0x") or len(tx_hash) != 66:
        raise ValueError("Invalid transaction hash")
    return SwapObservation(
        event_id=f"{tx_hash.lower()}:{log_index}",
        block_number=block,
        tx_hash=tx_hash.lower(),
        log_index=log_index,
        pool=spec.pool,
        symbol=spec.symbol,
        sender=_topic_address(topics[1], "sender"),
        recipient=_topic_address(topics[2], "recipient"),
        side=side,
        asset_amount=abs(base_raw) / (10 ** spec.base_decimals),
        quote_amount=abs(quote_raw) / (10 ** spec.quote_decimals),
    )


def enrich_observation(
    observation: SwapObservation,
    transaction: dict[str, Any],
    receipt: dict[str, Any],
    *,
    block_timestamp: int,
) -> SwapObservation:
    if not isinstance(transaction, dict) or transaction.get("hash", "").lower() != observation.tx_hash:
        raise ValueError("Transaction does not match observation")
    if _hex_int(transaction.get("blockNumber"), "transaction block") != observation.block_number:
        raise ValueError("Transaction block mismatch")
    if not isinstance(receipt, dict) or receipt.get("transactionHash", "").lower() != observation.tx_hash:
        raise ValueError("Receipt does not match observation")
    wallet = _address(transaction.get("from"), "transaction origin")
    gas_used = _hex_int(receipt.get("gasUsed"), "gasUsed")
    gas_price = _hex_int(receipt.get("effectiveGasPrice"), "effectiveGasPrice")
    timestamp = _nonnegative_int(block_timestamp, "block_timestamp")
    return replace(
        observation,
        wallet=wallet,
        network_fee_native=(gas_used * gas_price) / 1e18,
        ts=timestamp,
    )


def to_wallet_event(
    observation: SwapObservation,
    *,
    network_fee_quote: float | None,
    observed_at: int,
    finalized_at: int,
    source_version: str,
) -> WalletEvent:
    if observation.wallet is None or observation.ts is None:
        raise ValueError("Observation must be enriched before accounting")
    return WalletEvent(
        event_id=observation.event_id,
        wallet=observation.wallet,
        asset=observation.symbol.split("/", 1)[0],
        quote_asset=observation.symbol.split("/", 1)[1],
        ts=observation.ts,
        block_number=observation.block_number,
        tx_hash=observation.tx_hash,
        log_index=observation.log_index,
        side=observation.side,
        asset_amount=observation.asset_amount,
        quote_amount=observation.quote_amount,
        network_fee_quote=network_fee_quote,
        pool_fee_embedded=True,
        observed_at=observed_at,
        finalized_at=finalized_at,
        source_version=source_version,
    )


def latest_finalized_block(*, confirmations: int = 20, rpc: Callable[[str, list[Any]], Any] = rpc_call) -> int:
    if type(confirmations) is not int or confirmations < 0:
        raise ValueError("Invalid confirmations")
    head = _hex_int(rpc("eth_blockNumber", []), "block number")
    if head < confirmations:
        raise ValueError("Chain height below confirmation depth")
    return head - confirmations


def fetch_block_timestamp(block_number: int, *, rpc: Callable[[str, list[Any]], Any] = rpc_call) -> int:
    block = rpc("eth_getBlockByNumber", [hex(_nonnegative_int(block_number, "block_number")), False])
    if not isinstance(block, dict):
        raise ValueError("Malformed block")
    return _hex_int(block.get("timestamp"), "block timestamp")
