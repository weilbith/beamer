import json
import logging
import sys
from typing import List, TextIO

import structlog
from eth_utils import is_checksum_address, to_checksum_address

from beamer.typing import ChainId, ChecksumAddress


def setup_logging(log_level: str, log_json: bool) -> None:
    """Basic structlog setup"""

    logging.basicConfig(level=log_level, stream=sys.stdout, format="%(message)s")
    logging.logThreads = False

    logging.getLogger("web3").setLevel("INFO")
    logging.getLogger("urllib3").setLevel("INFO")

    shared_processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S.%f"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if log_json:
        processors = shared_processors + [structlog.processors.JSONRenderer()]
    else:
        processors = shared_processors + [structlog.dev.ConsoleRenderer()]

    structlog.configure(
        processors=processors,  # type: ignore
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


_Token = tuple[ChainId, ChecksumAddress]

# dictionary from base chain ID to deployed roll up IDs
SUPPORTED_CONNECTED_L2S = {
    # Mainnet
    1: frozenset({10, 42161, 288, 1088}),  # Optimism, Arbitrum, Boba, Metis
    # Rinkeby
    4: frozenset({421611, 28, 588}),  # Arbitrum, Boba, Metis
    # Goerli
    5: frozenset({420}),  # Optimism
    # Kovan
    42: frozenset({69}),  # Optimism
}


class TokenMatchChecker:
    def __init__(self, tokens: List[List[List[str]]]) -> None:
        # A mapping of tokens to equivalence classes. Each frozenset contains
        # tokens that are considered mutually equivalent.
        self._tokens: dict[_Token, frozenset[_Token]] = {}

        for token_mapping in tokens:
            equiv_class = frozenset(
                (ChainId(int(token[0])), to_checksum_address(token[1])) for token in token_mapping
            )
            l2_chain_ids = frozenset(chain_id for chain_id, _ in equiv_class)

            # check if equiv class contains chain ids from different base layers
            for connected_l2s in SUPPORTED_CONNECTED_L2S.values():
                intersection = connected_l2s.intersection(l2_chain_ids)
                if len(intersection) > 0:
                    msg = f"""All tokens' L2 chains must share the same base chain.
                     Please check {l2_chain_ids}"""
                    assert intersection == l2_chain_ids, msg

            for token in equiv_class:
                assert is_checksum_address(token[1])
                self._tokens[token] = equiv_class

    def is_valid_pair(
        self,
        source_chain_id: ChainId,
        source_token_address: ChecksumAddress,
        target_chain_id: ChainId,
        target_token_address: ChecksumAddress,
    ) -> bool:
        source_token = source_chain_id, source_token_address
        target_token = target_chain_id, target_token_address
        return target_token in self._tokens.get(source_token, frozenset())

    @staticmethod
    def from_file(f: TextIO) -> "TokenMatchChecker":
        tokens = json.load(f)
        return TokenMatchChecker(tokens)
