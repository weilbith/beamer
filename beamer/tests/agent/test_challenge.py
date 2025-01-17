import os
import time

import brownie
import pytest
from brownie import accounts
from eth_utils import to_checksum_address

import beamer.agent
from beamer.tests.util import EventCollector, HTTPProxy, earnings, make_request


@pytest.fixture(scope="module", autouse=True)
def _allow_unlisted_pairs():
    old = os.environ.get("BEAMER_ALLOW_UNLISTED_PAIRS")
    os.environ["BEAMER_ALLOW_UNLISTED_PAIRS"] = "1"
    yield
    if old is None:
        del os.environ["BEAMER_ALLOW_UNLISTED_PAIRS"]
    else:
        os.environ["BEAMER_ALLOW_UNLISTED_PAIRS"] = old


# Scenario 1:
#
# Bob              Charlie
# --------------------------
# claim
#                  challenge
#
# Winner: Charlie
def test_challenge_1(request_manager, token, config):
    target_address = accounts[8]
    requester, charlie = accounts[:2]

    agent = beamer.agent.Agent(config)
    agent.start()

    w3 = brownie.web3
    with earnings(w3, agent, num_fills=1) as agent_earnings, earnings(
        w3, charlie, num_fills=0
    ) as charlie_earnings:
        token.approve(request_manager.address, 1, {"from": agent.address})
        make_request(request_manager, token, requester, target_address, 1)

        collector = EventCollector(request_manager, "ClaimMade")

        claim = collector.next_event()
        assert claim is not None

        agent.stop()
        agent.wait()

        request_manager.challengeClaim(
            claim.claimId, {"from": charlie, "value": claim.claimerStake + 1}
        )

        claim = collector.next_event()
        assert claim is not None
        brownie.chain.mine(timestamp=claim.termination)
        request_manager.withdraw(claim.claimId, {"from": charlie})

    assert charlie_earnings() == claim.claimerStake
    assert agent_earnings() == -claim.claimerStake


# Scenario 2:
#
# Bob              Charlie
# --------------------------
# claim
#                  challenge
# challenge
#
# Winner: Bob
def test_challenge_2(request_manager, token, config):
    target_address = accounts[8]
    requester, charlie = accounts[:2]

    agent = beamer.agent.Agent(config)
    agent.start()

    w3 = brownie.web3
    with earnings(w3, agent, num_fills=1) as agent_earnings, earnings(
        w3, charlie, num_fills=0
    ) as charlie_earnings:
        token.approve(request_manager.address, 1, {"from": agent.address})
        make_request(request_manager, token, requester, target_address, 1)

        collector = EventCollector(request_manager, "ClaimMade")

        claim = collector.next_event()
        assert claim is not None

        request_manager.challengeClaim(
            claim.claimId, {"from": charlie, "value": claim.claimerStake + 1}
        )

        # Charlie's claim.
        claim = collector.next_event()
        assert claim is not None
        assert claim.claimerStake < claim.challengerStake

        # Bob's claim.
        claim = collector.next_event()
        assert claim is not None
        assert claim.claimerStake > claim.challengerStake

        brownie.chain.mine(timestamp=claim.termination)
        request_manager.withdraw(claim.claimId, {"from": agent.address})

        agent.stop()
        agent.wait()

    fees = request_manager.gasReimbursementFee() + request_manager.lpServiceFee()
    assert agent_earnings() == claim.challengerStake + fees
    assert charlie_earnings() == -claim.challengerStake


# Scenario 3:
#
# Bob              Charlie
# --------------------------
#                  claim
# challenge
#
# Winner: Bob
#
# Note: Bob is not filling the request here, merely noticing the dishonest
# claim and challenging it.
def test_challenge_3(request_manager, fill_manager, token, config):
    target_address = accounts[8]
    requester, charlie = accounts[:2]

    agent = beamer.agent.Agent(config)

    w3 = brownie.web3
    with earnings(w3, agent, num_fills=0) as agent_earnings, earnings(
        w3, charlie, num_fills=0
    ) as charlie_earnings:
        # Submit a request that Bob cannot fill.
        amount = token.balanceOf(agent.address) + 1
        request_id = make_request(request_manager, token, requester, target_address, amount)

        stake = request_manager.claimStake()
        request_manager.claimRequest(request_id, 0, {"from": charlie, "value": stake})

        collector = EventCollector(request_manager, "ClaimMade")
        collector.next_event()

        agent.start()

        # Get Bob's challenge.
        claim = collector.next_event()
        assert claim is not None
        assert claim.challengerStake > claim.claimerStake and claim.challenger == agent.address

        # Ensure that Bob did not fill the request.
        assert EventCollector(fill_manager, "RequestFilled").next_event(wait_time=2) is None

        brownie.chain.mine(timestamp=claim.termination)
        request_manager.withdraw(claim.claimId, {"from": agent.address})

        agent.stop()
        agent.wait()

    assert agent_earnings() == claim.claimerStake
    assert charlie_earnings() == -claim.claimerStake


# Scenario 4:
#
# Bob              Charlie
# --------------------------
#                  claim
# challenge
#                  challenge
#
# Winner: Charlie
#
# Note: Bob is not filling the request here, merely noticing the dishonest
# claim and challenging it.
def test_challenge_4(request_manager, fill_manager, token, config):
    target_address = accounts[8]
    requester, charlie = accounts[:2]

    agent = beamer.agent.Agent(config)

    w3 = brownie.web3
    with earnings(w3, agent, num_fills=0) as agent_earnings, earnings(
        w3, charlie, num_fills=0
    ) as charlie_earnings:
        # Submit a request that Bob cannot fill.
        amount = token.balanceOf(agent.address) + 1
        request_id = make_request(request_manager, token, requester, target_address, amount)

        stake = request_manager.claimStake()
        request_manager.claimRequest(request_id, 0, {"from": charlie, "value": stake})

        collector = EventCollector(request_manager, "ClaimMade")
        claim = collector.next_event()

        agent.start()

        # Get Bob's challenge.
        claim = collector.next_event()
        assert claim is not None
        assert claim.challengerStake > claim.claimerStake and claim.challenger == agent.address

        # Ensure that Bob did not fill the request.
        assert EventCollector(fill_manager, "RequestFilled").next_event(wait_time=2) is None

        agent.stop()
        agent.wait()

        request_manager.challengeClaim(
            claim.claimId, {"from": charlie, "value": claim.challengerStake + 1}
        )

        claim = collector.next_event()
        assert claim is not None
        assert claim.claimerStake > claim.challengerStake and claim.claimer == charlie.address

        brownie.chain.mine(timestamp=claim.termination)
        request_manager.withdraw(claim.claimId, {"from": charlie})

    fees = request_manager.gasReimbursementFee() + request_manager.lpServiceFee()
    assert agent_earnings() == -claim.challengerStake
    assert charlie_earnings() == claim.challengerStake + fees


# Scenario 5:
#
# Bob              Charlie
# --------------------------
#                  fill (if honest)
#                  claim
#
# ....fill_wait_time....
#
# challenge (if not honest)
#
#
# Note: This test tests if Bob waits `fill_wait_time` seconds before challenging
# a dishonest claim
@pytest.mark.parametrize("honest_claim", [True, False])
def test_challenge_5(request_manager, fill_manager, token, config, honest_claim):
    target_address = accounts[8]
    requester, charlie = accounts[:2]

    proxy_l2b = HTTPProxy(config.l2b_rpc_url)
    proxy_l2b.delay_rpc({"eth_getLogs": 3})
    proxy_l2b.start()

    l2b_rpc_url = "http://%s:%s" % (
        proxy_l2b.server_address[0],
        proxy_l2b.server_address[1],
    )

    config.l2b_rpc_url = l2b_rpc_url
    config.fill_wait_time = 6

    agent = beamer.agent.Agent(config)
    agent.start()

    fill_manager.addAllowedLP(charlie.address)

    # Submit a request that Bob cannot fill.
    amount = token.balanceOf(agent.address) + 1
    request_id = make_request(request_manager, token, requester, target_address, amount)
    fill_id = 0

    if honest_claim:
        # Fill by Charlie
        token.mint(charlie.address, amount, {"from": charlie.address})
        token.approve(fill_manager, amount, {"from": charlie.address})
        fill_transaction = fill_manager.fillRequest(
            request_id,
            brownie.chain.id,
            token.address,
            target_address,
            amount,
            {"from": charlie.address},
        )
        fill_id = fill_transaction.return_value

    # claim by Charlie
    stake = request_manager.claimStake()
    request_manager.claimRequest(request_id, fill_id, {"from": charlie.address, "value": stake})

    collector = EventCollector(request_manager, "ClaimMade")
    claim = collector.next_event()
    assert claim is not None

    # Wait just before the challenge back off time
    time.sleep(config.fill_wait_time - 1)

    # Regardless of the honesty of the claim there should be no challenge event
    claim = collector.next_event(0.1)
    assert claim is None

    claim = collector.next_event()
    if honest_claim:
        # No challenge received
        assert claim is None
    else:
        # Challenge expected
        assert claim is not None
        assert claim.challenger == to_checksum_address(agent.address)

    agent.stop()
    proxy_l2b.stop()
    agent.wait()
