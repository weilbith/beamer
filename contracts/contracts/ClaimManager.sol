// SPDX-License-Identifier: MIT
pragma solidity ^0.8.7;

import "OpenZeppelin/openzeppelin-contracts@4.3.2/contracts/access/Ownable.sol";
import "OpenZeppelin/openzeppelin-contracts@4.3.2/contracts/utils/math/SafeMath.sol";
import "OpenZeppelin/openzeppelin-contracts@4.3.2/contracts/utils/math/Math.sol";


contract ClaimManager is Ownable{

    using SafeMath for uint256;
    using Math for uint256;

    struct Claim {
        uint256 requestId;
        address claimer;
        uint256 termination;
    }

    struct Challenge {
        address challenger;
        uint256 challengerStake;
        uint256 claimerStake;
        uint256 termination;
    }

    event ClaimCreated(
        uint256 indexed claimId,
        uint256 requestId,
        address claimer,
        uint256 termination
    );

    event ChallengeOutbid(
        uint256 indexed claimId,
        address leader,
        uint256 highestBid
    );

    event ClaimChallenged(
        uint256 indexed claimId,
        address challenger
    );


    uint256 public claimStake;
    uint256 public claimPeriod;
    mapping (uint256 => Claim) public claims;
    uint256 public claimCounter;

    uint256 public challengePeriod;
    uint256 public challengeExtensionTime;
    mapping (uint256 => Challenge) public challenges;

    constructor(uint256 _claimStake, uint256 _claimPeriod, uint256 _challengePeriod, uint256 _challengeExtensionTime) {
        claimStake = _claimStake;
        claimPeriod = _claimPeriod;
        challengePeriod = _challengePeriod;
        challengeExtensionTime = _challengeExtensionTime;
    }


    modifier validClaimId(uint256 claimId){
        require(claimId <= claimCounter && claimId > 0, "claimId not valid");
        _;
    }

    function claimRequest(uint256 requestId) external payable returns (uint256){
        require(msg.value == claimStake, "Stake provided not correct");
        claimCounter += 1;
        uint256 newClaimId = claimCounter;
        Claim storage newClaim = claims[claimCounter];
        newClaim.requestId = requestId;
        newClaim.claimer = msg.sender;
        newClaim.termination = block.number + claimPeriod;

        emit ClaimCreated(
            newClaimId,
            requestId,
            newClaim.claimer,
            newClaim.termination
        );

        return claimCounter;
    }

    function claimSuccessful(uint256 claimId) public view validClaimId(claimId) returns (bool){
        require(challenges[claimId].termination == 0 , "Claim was challenged");

        return block.number >= claims[claimId].termination;
    }

    function challengeClaim(uint256 claimId) external validClaimId(claimId) payable{
        Challenge storage challenge = challenges[claimId];

        require(challenge.challenger == address(0), "Already challenged");
        require(block.number < claims[claimId].termination, "Already claimed successfully");
        require(msg.value > claimStake, "Not enough funds provided");

        challenge.challenger = msg.sender;
        challenge.challengerStake = msg.value;
        challenge.claimerStake = claimStake;
        challenge.termination = challengePeriod;

        emit ClaimChallenged(
            claimId,
            msg.sender
        );
    }

    function outbidChallenge(uint claimId) external validClaimId(claimId) payable {
        Claim storage claim = claims[claimId];
        Challenge storage challenge = challenges[claimId];
        require(challenge.challenger != address(0), "Claim not yet challenged");
        require(msg.sender == claim.claimer || msg.sender == challenge.challenger,"Already challenged by another address");

        bool claimerStakeBigger = challenge.claimerStake > challenge.challengerStake;
        address nextActor = claimerStakeBigger ? claim.claimer : challenge.challenger;
        require(msg.sender == nextActor, "Not eligible to outbid");

        uint256 minStake = claimerStakeBigger ? challenge.claimerStake - challenge.challengerStake : challenge.challengerStake - challenge.claimerStake;
        require(msg.value > minStake, "Not enough funds provided");

        if(msg.sender == claim.claimer){
            challenge.challengerStake += msg.value;
        }
        else{
            challenge.claimerStake += msg.value;
        }

        challenge.termination = Math.max(challenge.termination, block.number + challengeExtensionTime);

        emit ChallengeOutbid(
            claimId,
            msg.sender,
            Math.max(challenge.challengerStake, challenge.claimerStake)
        );
    }
}