import brownie
from brownie import accounts, chain, web3

from contracts.tests.utils import make_request


RM_FIELD_LP_FEE = 9
RM_FIELD_RAISYNC_FEE = 10


def test_fee_split_works(request_manager, token, claim_stake, claim_period):
    requester, claimer = accounts[:2]
    transfer_amount = 23

    request_id = make_request(request_manager, token, requester, transfer_amount, zero_fees=False)

    reimbursement_fee = request_manager.gasReimbursementFee()
    lp_service_fee = request_manager.lpServiceFee()
    raisync_fee = request_manager.raisyncServiceFee()
    assert raisync_fee > 0

    # The request is not claimed yet, so no raisync fee has been collected yet
    assert request_manager.collectedRaisyncFees() == 0
    assert (
        request_manager.requests(request_id)[RM_FIELD_LP_FEE] == reimbursement_fee + lp_service_fee
    )
    assert request_manager.requests(request_id)[RM_FIELD_RAISYNC_FEE] == raisync_fee

    claim_tx = request_manager.claimRequest(request_id, {"from": claimer, "value": claim_stake})
    claim_id = claim_tx.return_value

    # Timetravel after claim period
    chain.mine(timedelta=claim_period)

    # Even if the requester calls withdraw, the funds go to the claimer
    withdraw_tx = request_manager.withdraw(claim_id, {"from": requester})
    assert "ClaimWithdrawn" in withdraw_tx.events

    assert request_manager.collectedRaisyncFees() == raisync_fee
    assert request_manager.requests(request_id)[9] == reimbursement_fee + lp_service_fee
    assert request_manager.requests(request_id)[10] == raisync_fee


def test_raisync_service_fee_withdrawable_by_owner(
    request_manager, token, claim_stake, claim_period
):
    owner, requester, claimer = accounts[:3]
    raisync_fee = request_manager.raisyncServiceFee()
    request_id = make_request(request_manager, token, requester, 23, zero_fees=False)

    with brownie.reverts("Ownable: caller is not the owner"):
        request_manager.withdrawRaisyncFees({"from": requester})

    assert request_manager.collectedRaisyncFees() == 0
    with brownie.reverts("Zero fees available"):
        request_manager.withdrawRaisyncFees({"from": owner})

    claim_tx = request_manager.claimRequest(request_id, {"from": claimer, "value": claim_stake})
    claim_id = claim_tx.return_value

    chain.mine(timedelta=claim_period)

    assert request_manager.collectedRaisyncFees() == 0
    with brownie.reverts("Zero fees available"):
        request_manager.withdrawRaisyncFees({"from": owner})

    request_manager.withdraw(claim_id, {"from": requester})

    owner_eth = web3.eth.get_balance(owner.address)

    request_manager.withdrawRaisyncFees({"from": owner})
    assert web3.eth.get_balance(owner.address) == owner_eth + raisync_fee


def test_fee_gas_price_updatable_by_owner(request_manager, token):
    owner, requester = accounts[:2]
    make_request(request_manager, token, requester, 23, zero_fees=False)

    old_gas_price = request_manager.gasPrice()
    old_fee = request_manager.totalFee()

    new_gas_price = old_gas_price * 2

    with brownie.reverts("Ownable: caller is not the owner"):
        request_manager.updateGasPrice(new_gas_price, {"from": requester})

    request_manager.updateGasPrice(new_gas_price, {"from": owner})
    assert request_manager.gasPrice() == new_gas_price
    assert request_manager.totalFee() == 2 * old_fee


def test_fee_reimbursed_on_cancellation(request_manager, token, cancellation_period):
    _, requester = accounts[:2]
    transfer_amount = 23

    requester_eth = web3.eth.get_balance(requester.address)

    request_id = make_request(request_manager, token, requester, transfer_amount, zero_fees=False)

    total_fee = request_manager.totalFee()
    assert total_fee > 0
    assert web3.eth.get_balance(requester.address) == requester_eth - total_fee

    request_manager.cancelRequest(request_id, {"from": requester})

    assert request_manager.collectedRaisyncFees() == 0

    # Timetravel after cancellation period
    chain.mine(timedelta=cancellation_period)

    request_manager.withdrawCancelledRequest(request_id, {"from": requester})
    assert request_manager.collectedRaisyncFees() == 0
    assert web3.eth.get_balance(requester.address) == requester_eth

    assert token.balanceOf(requester) == transfer_amount
