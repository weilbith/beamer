import time
from dataclasses import dataclass
from typing import Optional

import requests.exceptions
import structlog
import web3
from eth_abi.codec import ABICodec
from eth_utils.abi import event_abi_to_log_topic
from web3.contract import Contract, get_event_data
from web3.types import ABIEvent, BlockData, ChecksumAddress, FilterParams, LogReceipt, Wei

from beamer.typing import (
    BlockNumber,
    ChainId,
    ClaimId,
    FillId,
    RequestId,
    Termination,
    TokenAmount,
)


@dataclass(frozen=True)
class Event:
    chain_id: ChainId


@dataclass(frozen=True)
class LatestBlockUpdatedEvent(Event):
    block_data: BlockData


@dataclass(frozen=True)
class RequestEvent(Event):
    request_id: RequestId


@dataclass(frozen=True)
class RequestCreated(RequestEvent):
    target_chain_id: ChainId
    source_token_address: ChecksumAddress
    target_token_address: ChecksumAddress
    target_address: ChecksumAddress
    amount: TokenAmount
    valid_until: Termination


@dataclass(frozen=True)
class RequestFilled(RequestEvent):
    fill_id: FillId
    source_chain_id: ChainId
    target_token_address: ChecksumAddress
    filler: ChecksumAddress
    amount: TokenAmount


@dataclass(frozen=True)
class DepositWithdrawn(RequestEvent):
    receiver: ChecksumAddress


@dataclass(frozen=True)
class ClaimEvent(Event):
    claim_id: ClaimId


@dataclass(frozen=True)
class ClaimMade(ClaimEvent):
    request_id: RequestId
    fill_id: FillId
    claimer: ChecksumAddress
    claimer_stake: Wei
    challenger: ChecksumAddress
    challenger_stake: Wei
    termination: Termination


@dataclass(frozen=True)
class ClaimWithdrawn(ClaimEvent):
    request_id: RequestId
    claim_receiver: ChecksumAddress


def _camel_to_snake(s: str) -> str:
    return "".join("_" + c.lower() if c.isupper() else c for c in s).lstrip("_")


_EVENT_TYPES = dict(
    RequestCreated=RequestCreated,
    RequestFilled=RequestFilled,
    DepositWithdrawn=DepositWithdrawn,
    ClaimMade=ClaimMade,
    ClaimWithdrawn=ClaimWithdrawn,
)


def _make_topics_to_abi(contract: web3.contract.Contract) -> dict[bytes, ABIEvent]:
    event_abis = {}
    for abi in contract.abi:
        if abi["type"] == "event":
            event_abis[event_abi_to_log_topic(abi)] = abi  # type: ignore
    return event_abis


def _decode_event(
    codec: ABICodec, log_entry: LogReceipt, chain_id: ChainId, event_abis: dict[bytes, ABIEvent]
) -> Optional[Event]:
    topic = log_entry["topics"][0]
    event_abi = event_abis[topic]
    data = get_event_data(abi_codec=codec, event_abi=event_abi, log_entry=log_entry)
    if data.event in _EVENT_TYPES:
        kwargs = {_camel_to_snake(name): value for name, value in data.args.items()}
        kwargs["chain_id"] = chain_id
        return _EVENT_TYPES[data.event](**kwargs)
    return None


def _decode_events(
    logs: list[LogReceipt], codec: ABICodec, chain_id: ChainId, event_abis: dict[bytes, ABIEvent]
) -> list[Event]:
    events = []
    for entry in logs:
        event = _decode_event(codec, entry, chain_id, event_abis)
        if event is not None:
            events.append(event)
    return events


class EventFetcher:
    _DEFAULT_BLOCKS = 1_000
    _MIN_BLOCKS = 2
    _MAX_BLOCKS = 100_000
    _ETH_GET_LOGS_THRESHOLD_FAST = 2
    _ETH_GET_LOGS_THRESHOLD_SLOW = 5

    def __init__(self, contract_name: str, contract: Contract, start_block: BlockNumber):
        self._contract_name = contract_name
        self._contract = contract
        self._next_block_number = start_block
        self._blocks_to_fetch = EventFetcher._DEFAULT_BLOCKS
        self._chain_id = ChainId(contract.web3.eth.chain_id)
        self._event_abis = _make_topics_to_abi(contract)
        self._log = structlog.get_logger(type(self).__name__)

    def _fetch_range(
        self, from_block: BlockNumber, to_block: BlockNumber
    ) -> Optional[list[Event]]:
        """Returns a list of events that happened in the period [from_block, to_block],
        or None if a timeout occurs."""
        self._log.debug(
            "Fetching events",
            chain_id=self._chain_id,
            contract=self._contract_name,
            from_block=from_block,
            to_block=to_block,
        )
        try:
            before_query = time.monotonic()
            params: FilterParams = dict(
                fromBlock=from_block, toBlock=to_block, address=self._contract.address
            )
            logs = self._contract.web3.eth.get_logs(params)
            after_query = time.monotonic()

        # Boba limits the range to 5000 blocks
        # 'ValueError: {'code': -32000, 'message': 'exceed maximum block range: 5000'}'
        except (requests.exceptions.ReadTimeout, ValueError):
            old = self._blocks_to_fetch
            self._blocks_to_fetch = max(EventFetcher._MIN_BLOCKS, old // 5)
            self._log.debug(
                "Failed to get events in time, reducing number of blocks",
                chain_id=self._chain_id,
                old=old,
                new=self._blocks_to_fetch,
            )
            return None

        except requests.exceptions.ConnectionError as exc:
            assert isinstance(self._contract.web3.provider, web3.HTTPProvider)
            url = self._contract.web3.provider.endpoint_uri
            self._log.error("Connection error", url=url, exc=exc)
            # Propagate the exception upwards so we don't make further attempts.
            raise exc

        else:
            duration = after_query - before_query
            if duration < EventFetcher._ETH_GET_LOGS_THRESHOLD_FAST:
                self._blocks_to_fetch = min(EventFetcher._MAX_BLOCKS, self._blocks_to_fetch * 2)
            elif duration > EventFetcher._ETH_GET_LOGS_THRESHOLD_SLOW:
                self._blocks_to_fetch = max(EventFetcher._MIN_BLOCKS, self._blocks_to_fetch // 2)
            codec = self._contract.web3.codec
            return _decode_events(logs, codec, self._chain_id, self._event_abis)

    def fetch(self) -> list[Event]:
        try:
            block_number = self._contract.web3.eth.block_number
        except requests.exceptions.RequestException:
            return []

        if block_number < self._next_block_number:
            return []

        result = []
        from_block = self._next_block_number
        while from_block <= block_number:
            to_block = min(block_number, BlockNumber(from_block + self._blocks_to_fetch))
            try:
                events = self._fetch_range(from_block, to_block)
            except requests.exceptions.ConnectionError:
                break
            if events is not None:
                result.extend(events)
                from_block = BlockNumber(to_block + 1)

        self._next_block_number = from_block
        try:
            # Block number needs to be decremented here, because it is already incremented above
            block_data = self._contract.web3.eth.get_block(from_block - 1)
        except requests.exceptions.RequestException:
            return result
        else:
            result.append(
                LatestBlockUpdatedEvent(
                    chain_id=self._chain_id,
                    block_data=block_data,
                )
            )
        return result
