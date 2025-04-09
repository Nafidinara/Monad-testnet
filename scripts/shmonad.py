import os
import random
import time
from colorama import init, Fore, Style
from web3 import Web3

# Initialize colorama
init(autoreset=True)

# Constants
RPC_URL = "https://testnet-rpc.monad.xyz/"
EXPLORER_URL = "https://testnet.monadexplorer.com/tx/0x"
SHMONAD_ADDRESS = "0x3a98250F98Dd388C211206983453837C8365BDc1"
STAKE_POLICY_ID = 4
CHAIN_ID = 10143  # Monad testnet chain ID
# Constants (tambahkan setelah CHAIN_ID)
MAX_UINT256 = 2**256 - 1  # Nilai maksimum untuk approve

# Full contract ABI
SHMONAD_ABI = [
    {
        "type": "constructor",
        "inputs": [{"name": "addressHub", "type": "address", "internalType": "address"}],
        "stateMutability": "nonpayable"
    },
    {
        "type": "function",
        "name": "ADDRESS_HUB",
        "inputs": [],
        "outputs": [{"name": "", "type": "address", "internalType": "address"}],
        "stateMutability": "view"
    },
    {
        "type": "function",
        "name": "DOMAIN_SEPARATOR",
        "inputs": [],
        "outputs": [{"name": "", "type": "bytes32", "internalType": "bytes32"}],
        "stateMutability": "view"
    },
    {
        "type": "function",
        "name": "addPolicyAgent",
        "inputs": [
            {"name": "policyID", "type": "uint64", "internalType": "uint64"},
            {"name": "agent", "type": "address", "internalType": "address"}
        ],
        "outputs": [],
        "stateMutability": "nonpayable"
    },
    {
        "type": "function",
        "name": "agentExecuteWithSponsor",
        "inputs": [
            {"name": "policyID", "type": "uint64", "internalType": "uint64"},
            {"name": "payor", "type": "address", "internalType": "address"},
            {"name": "recipient", "type": "address", "internalType": "address"},
            {"name": "msgValue", "type": "uint256", "internalType": "uint256"},
            {"name": "gasLimit", "type": "uint256", "internalType": "uint256"},
            {"name": "callTarget", "type": "address", "internalType": "address"},
            {"name": "callData", "type": "bytes", "internalType": "bytes"}
        ],
        "outputs": [
            {"name": "actualPayorCost", "type": "uint128", "internalType": "uint128"},
            {"name": "success", "type": "bool", "internalType": "bool"},
            {"name": "returnData", "type": "bytes", "internalType": "bytes"}
        ],
        "stateMutability": "payable"
    },
    {
        "type": "function",
        "name": "agentTransferFromBonded",
        "inputs": [
            {"name": "policyID", "type": "uint64", "internalType": "uint64"},
            {"name": "from", "type": "address", "internalType": "address"},
            {"name": "to", "type": "address", "internalType": "address"},
            {"name": "amount", "type": "uint256", "internalType": "uint256"},
            {"name": "fromReleaseAmount", "type": "uint256", "internalType": "uint256"},
            {"name": "inUnderlying", "type": "bool", "internalType": "bool"}
        ],
        "outputs": [],
        "stateMutability": "nonpayable"
    },
    {
        "type": "function",
        "name": "agentUnbond",
        "inputs": [
            {"name": "policyID", "type": "uint64", "internalType": "uint64"},
            {"name": "from", "type": "address", "internalType": "address"},
            {"name": "amount", "type": "uint256", "internalType": "uint256"},
            {"name": "fromReleaseAmount", "type": "uint256", "internalType": "uint256"},
            {"name": "inUnderlying", "type": "bool", "internalType": "bool"}
        ],
        "outputs": [],
        "stateMutability": "nonpayable"
    },
    {
        "type": "function",
        "name": "agentWithdrawFromBonded",
        "inputs": [
            {"name": "policyID", "type": "uint64", "internalType": "uint64"},
            {"name": "from", "type": "address", "internalType": "address"},
            {"name": "to", "type": "address", "internalType": "address"},
            {"name": "amount", "type": "uint256", "internalType": "uint256"},
            {"name": "fromReleaseAmount", "type": "uint256", "internalType": "uint256"},
            {"name": "inUnderlying", "type": "bool", "internalType": "bool"}
        ],
        "outputs": [],
        "stateMutability": "nonpayable"
    },
    {
        "type": "function",
        "name": "allowance",
        "inputs": [
            {"name": "owner", "type": "address", "internalType": "address"},
            {"name": "spender", "type": "address", "internalType": "address"}
        ],
        "outputs": [{"name": "", "type": "uint256", "internalType": "uint256"}],
        "stateMutability": "view"
    },
    {
        "type": "function",
        "name": "approve",
        "inputs": [
            {"name": "spender", "type": "address", "internalType": "address"},
            {"name": "value", "type": "uint256", "internalType": "uint256"}
        ],
        "outputs": [{"name": "", "type": "bool", "internalType": "bool"}],
        "stateMutability": "nonpayable"
    },
    {
        "type": "function",
        "name": "asset",
        "inputs": [],
        "outputs": [{"name": "", "type": "address", "internalType": "address"}],
        "stateMutability": "view"
    },
    {
        "type": "function",
        "name": "balanceOf",
        "inputs": [{"name": "account", "type": "address", "internalType": "address"}],
        "outputs": [{"name": "", "type": "uint256", "internalType": "uint256"}],
        "stateMutability": "view"
    },
    {
        "type": "function",
        "name": "balanceOfBonded",
        "inputs": [{"name": "account", "type": "address", "internalType": "address"}],
        "outputs": [{"name": "", "type": "uint256", "internalType": "uint256"}],
        "stateMutability": "view"
    },
    {
        "type": "function",
        "name": "balanceOfBonded",
        "inputs": [
            {"name": "policyID", "type": "uint64", "internalType": "uint64"},
            {"name": "account", "type": "address", "internalType": "address"}
        ],
        "outputs": [{"name": "", "type": "uint256", "internalType": "uint256"}],
        "stateMutability": "view"
    },
    {
        "type": "function",
        "name": "balanceOfUnbonding",
        "inputs": [
            {"name": "policyID", "type": "uint64", "internalType": "uint64"},
            {"name": "account", "type": "address", "internalType": "address"}
        ],
        "outputs": [{"name": "", "type": "uint256", "internalType": "uint256"}],
        "stateMutability": "view"
    },
    {
        "type": "function",
        "name": "batchHold",
        "inputs": [
            {"name": "policyID", "type": "uint64", "internalType": "uint64"},
            {"name": "accounts", "type": "address[]", "internalType": "address[]"},
            {"name": "amounts", "type": "uint256[]", "internalType": "uint256[]"}
        ],
        "outputs": [],
        "stateMutability": "nonpayable"
    },
    {
        "type": "function",
        "name": "batchRelease",
        "inputs": [
            {"name": "policyID", "type": "uint64", "internalType": "uint64"},
            {"name": "accounts", "type": "address[]", "internalType": "address[]"},
            {"name": "amounts", "type": "uint256[]", "internalType": "uint256[]"}
        ],
        "outputs": [],
        "stateMutability": "nonpayable"
    },
    {
        "type": "function",
        "name": "bond",
        "inputs": [
            {"name": "policyID", "type": "uint64", "internalType": "uint64"},
            {"name": "bondRecipient", "type": "address", "internalType": "address"},
            {"name": "amount", "type": "uint256", "internalType": "uint256"}
        ],
        "outputs": [],
        "stateMutability": "nonpayable"
    },
    {
        "type": "function",
        "name": "bondedTotalSupply",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256", "internalType": "uint256"}],
        "stateMutability": "view"
    },
    {
        "type": "function",
        "name": "boostYield",
        "inputs": [
            {"name": "shMonAmount", "type": "uint256", "internalType": "uint256"},
            {"name": "from", "type": "address", "internalType": "address"}
        ],
        "outputs": [],
        "stateMutability": "nonpayable"
    },
    {
        "type": "function",
        "name": "boostYield",
        "inputs": [],
        "outputs": [],
        "stateMutability": "payable"
    },
    {
        "type": "function",
        "name": "claim",
        "inputs": [
            {"name": "policyID", "type": "uint64", "internalType": "uint64"},
            {"name": "amount", "type": "uint256", "internalType": "uint256"}
        ],
        "outputs": [],
        "stateMutability": "nonpayable"
    },
    {
        "type": "function",
        "name": "claimAndRebond",
        "inputs": [
            {"name": "fromPolicyID", "type": "uint64", "internalType": "uint64"},
            {"name": "toPolicyID", "type": "uint64", "internalType": "uint64"},
            {"name": "bondRecipient", "type": "address", "internalType": "address"},
            {"name": "amount", "type": "uint256", "internalType": "uint256"}
        ],
        "outputs": [],
        "stateMutability": "nonpayable"
    },
    {
        "type": "function",
        "name": "claimAndWithdraw",
        "inputs": [
            {"name": "policyID", "type": "uint64", "internalType": "uint64"},
            {"name": "amount", "type": "uint256", "internalType": "uint256"}
        ],
        "outputs": [{"name": "shares", "type": "uint256", "internalType": "uint256"}],
        "stateMutability": "nonpayable"
    },
    {
        "type": "function",
        "name": "convertToAssets",
        "inputs": [{"name": "shares", "type": "uint256", "internalType": "uint256"}],
        "outputs": [{"name": "", "type": "uint256", "internalType": "uint256"}],
        "stateMutability": "view"
    },
    {
        "type": "function",
        "name": "convertToShares",
        "inputs": [{"name": "assets", "type": "uint256", "internalType": "uint256"}],
        "outputs": [{"name": "", "type": "uint256", "internalType": "uint256"}],
        "stateMutability": "view"
    },
    {
        "type": "function",
        "name": "createPolicy",
        "inputs": [{"name": "escrowDuration", "type": "uint48", "internalType": "uint48"}],
        "outputs": [
            {"name": "policyID", "type": "uint64", "internalType": "uint64"},
            {"name": "policyERC20Wrapper", "type": "address", "internalType": "address"}
        ],
        "stateMutability": "nonpayable"
    },
    {
        "type": "function",
        "name": "decimals",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint8", "internalType": "uint8"}],
        "stateMutability": "view"
    },
    {
        "type": "function",
        "name": "deposit",
        "inputs": [
            {"name": "assets", "type": "uint256", "internalType": "uint256"},
            {"name": "receiver", "type": "address", "internalType": "address"}
        ],
        "outputs": [{"name": "", "type": "uint256", "internalType": "uint256"}],
        "stateMutability": "payable"
    },
    {
        "type": "function",
        "name": "depositAndBond",
        "inputs": [
            {"name": "policyID", "type": "uint64", "internalType": "uint64"},
            {"name": "bondRecipient", "type": "address", "internalType": "address"},
            {"name": "shMonToBond", "type": "uint256", "internalType": "uint256"}
        ],
        "outputs": [],
        "stateMutability": "payable"
    },
    {
        "type": "function",
        "name": "disablePolicy",
        "inputs": [{"name": "policyID", "type": "uint64", "internalType": "uint64"}],
        "outputs": [],
        "stateMutability": "nonpayable"
    },
    {
        "type": "function",
        "name": "eip712Domain",
        "inputs": [],
        "outputs": [
            {"name": "fields", "type": "bytes1", "internalType": "bytes1"},
            {"name": "name", "type": "string", "internalType": "string"},
            {"name": "version", "type": "string", "internalType": "string"},
            {"name": "chainId", "type": "uint256", "internalType": "uint256"},
            {"name": "verifyingContract", "type": "address", "internalType": "address"},
            {"name": "salt", "type": "bytes32", "internalType": "bytes32"},
            {"name": "extensions", "type": "uint256[]", "internalType": "uint256[]"}
        ],
        "stateMutability": "view"
    },
    {
        "type": "function",
        "name": "getHoldAmount",
        "inputs": [
            {"name": "policyID", "type": "uint64", "internalType": "uint64"},
            {"name": "account", "type": "address", "internalType": "address"}
        ],
        "outputs": [{"name": "", "type": "uint256", "internalType": "uint256"}],
        "stateMutability": "view"
    },
    {
        "type": "function",
        "name": "getPolicy",
        "inputs": [{"name": "policyID", "type": "uint64", "internalType": "uint64"}],
        "outputs": [
            {
                "name": "",
                "type": "tuple",
                "internalType": "struct Policy",
                "components": [
                    {"name": "escrowDuration", "type": "uint48", "internalType": "uint48"},
                    {"name": "active", "type": "bool", "internalType": "bool"}
                ]
            }
        ],
        "stateMutability": "view"
    },
    {
        "type": "function",
        "name": "getPolicyAgents",
        "inputs": [{"name": "policyID", "type": "uint64", "internalType": "uint64"}],
        "outputs": [{"name": "", "type": "address[]", "internalType": "address[]"}],
        "stateMutability": "view"
    },
    {
        "type": "function",
        "name": "hold",
        "inputs": [
            {"name": "policyID", "type": "uint64", "internalType": "uint64"},
            {"name": "account", "type": "address", "internalType": "address"},
            {"name": "amount", "type": "uint256", "internalType": "uint256"}
        ],
        "outputs": [],
        "stateMutability": "nonpayable"
    },
    {
        "type": "function",
        "name": "initialize",
        "inputs": [{"name": "deployer", "type": "address", "internalType": "address"}],
        "outputs": [],
        "stateMutability": "nonpayable"
    },
    {
        "type": "function",
        "name": "isPolicyAgent",
        "inputs": [
            {"name": "policyID", "type": "uint64", "internalType": "uint64"},
            {"name": "agent", "type": "address", "internalType": "address"}
        ],
        "outputs": [{"name": "", "type": "bool", "internalType": "bool"}],
        "stateMutability": "view"
    },
    {
        "type": "function",
        "name": "maxDeposit",
        "inputs": [{"name": "", "type": "address", "internalType": "address"}],
        "outputs": [{"name": "", "type": "uint256", "internalType": "uint256"}],
        "stateMutability": "view"
    },
    {
        "type": "function",
        "name": "maxMint",
        "inputs": [{"name": "", "type": "address", "internalType": "address"}],
        "outputs": [{"name": "", "type": "uint256", "internalType": "uint256"}],
        "stateMutability": "view"
    },
    {
        "type": "function",
        "name": "maxRedeem",
        "inputs": [{"name": "owner", "type": "address", "internalType": "address"}],
        "outputs": [{"name": "", "type": "uint256", "internalType": "uint256"}],
        "stateMutability": "view"
    },
    {
        "type": "function",
        "name": "maxWithdraw",
        "inputs": [{"name": "owner", "type": "address", "internalType": "address"}],
        "outputs": [{"name": "", "type": "uint256", "internalType": "uint256"}],
        "stateMutability": "view"
    },
    {
        "type": "function",
        "name": "mint",
        "inputs": [
            {"name": "shares", "type": "uint256", "internalType": "uint256"},
            {"name": "receiver", "type": "address", "internalType": "address"}
        ],
        "outputs": [{"name": "", "type": "uint256", "internalType": "uint256"}],
        "stateMutability": "payable"
    },
    {
        "type": "function",
        "name": "name",
        "inputs": [],
        "outputs": [{"name": "", "type": "string", "internalType": "string"}],
        "stateMutability": "view"
    },
    {
        "type": "function",
        "name": "nonces",
        "inputs": [{"name": "owner", "type": "address", "internalType": "address"}],
        "outputs": [{"name": "", "type": "uint256", "internalType": "uint256"}],
        "stateMutability": "view"
    },
    {
        "type": "function",
        "name": "permit",
        "inputs": [
            {"name": "owner", "type": "address", "internalType": "address"},
            {"name": "spender", "type": "address", "internalType": "address"},
            {"name": "value", "type": "uint256", "internalType": "uint256"},
            {"name": "deadline", "type": "uint256", "internalType": "uint256"},
            {"name": "v", "type": "uint8", "internalType": "uint8"},
            {"name": "r", "type": "bytes32", "internalType": "bytes32"},
            {"name": "s", "type": "bytes32", "internalType": "bytes32"}
        ],
        "outputs": [],
        "stateMutability": "nonpayable"
    },
    {
        "type": "function",
        "name": "policyCount",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint64", "internalType": "uint64"}],
        "stateMutability": "view"
    },
    {
        "type": "function",
        "name": "previewDeposit",
        "inputs": [{"name": "assets", "type": "uint256", "internalType": "uint256"}],
        "outputs": [{"name": "", "type": "uint256", "internalType": "uint256"}],
        "stateMutability": "view"
    },
    {
        "type": "function",
        "name": "previewMint",
        "inputs": [{"name": "shares", "type": "uint256", "internalType": "uint256"}],
        "outputs": [{"name": "", "type": "uint256", "internalType": "uint256"}],
        "stateMutability": "view"
    },
    {
        "type": "function",
        "name": "previewRedeem",
        "inputs": [{"name": "shares", "type": "uint256", "internalType": "uint256"}],
        "outputs": [{"name": "", "type": "uint256", "internalType": "uint256"}],
        "stateMutability": "view"
    },
    {
        "type": "function",
        "name": "previewWithdraw",
        "inputs": [{"name": "assets", "type": "uint256", "internalType": "uint256"}],
        "outputs": [{"name": "", "type": "uint256", "internalType": "uint256"}],
        "stateMutability": "view"
    },
    {
        "type": "function",
        "name": "redeem",
        "inputs": [
            {"name": "shares", "type": "uint256", "internalType": "uint256"},
            {"name": "receiver", "type": "address", "internalType": "address"},
            {"name": "owner", "type": "address", "internalType": "address"}
        ],
        "outputs": [{"name": "", "type": "uint256", "internalType": "uint256"}],
        "stateMutability": "nonpayable"
    },
    {
        "type": "function",
        "name": "release",
        "inputs": [
            {"name": "policyID", "type": "uint64", "internalType": "uint64"},
            {"name": "account", "type": "address", "internalType": "address"},
            {"name": "amount", "type": "uint256", "internalType": "uint256"}
        ],
        "outputs": [],
        "stateMutability": "nonpayable"
    },
    {
        "type": "function",
        "name": "removePolicyAgent",
        "inputs": [
            {"name": "policyID", "type": "uint64", "internalType": "uint64"},
            {"name": "agent", "type": "address", "internalType": "address"}
        ],
        "outputs": [],
        "stateMutability": "nonpayable"
    },
    {
        "type": "function",
        "name": "setMinBondedBalance",
        "inputs": [
            {"name": "policyID", "type": "uint64", "internalType": "uint64"},
            {"name": "minBonded", "type": "uint128", "internalType": "uint128"},
            {"name": "maxTopUpPerPeriod", "type": "uint128", "internalType": "uint128"},
            {"name": "topUpPeriodDuration", "type": "uint32", "internalType": "uint32"}
        ],
        "outputs": [],
        "stateMutability": "nonpayable"
    },
    {
        "type": "function",
        "name": "symbol",
        "inputs": [],
        "outputs": [{"name": "", "type": "string", "internalType": "string"}],
        "stateMutability": "view"
    },
    {
        "type": "function",
        "name": "totalAssets",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256", "internalType": "uint256"}],
        "stateMutability": "view"
    },
    {
        "type": "function",
        "name": "totalSupply",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256", "internalType": "uint256"}],
        "stateMutability": "view"
    },
    {
        "type": "function",
        "name": "transfer",
        "inputs": [
            {"name": "to", "type": "address", "internalType": "address"},
            {"name": "value", "type": "uint256", "internalType": "uint256"}
        ],
        "outputs": [{"name": "", "type": "bool", "internalType": "bool"}],
        "stateMutability": "nonpayable"
    },
    {
        "type": "function",
        "name": "transferFrom",
        "inputs": [
            {"name": "from", "type": "address", "internalType": "address"},
            {"name": "to", "type": "address", "internalType": "address"},
            {"name": "value", "type": "uint256", "internalType": "uint256"}
        ],
        "outputs": [{"name": "", "type": "bool", "internalType": "bool"}],
        "stateMutability": "nonpayable"
    },
    {
        "type": "function",
        "name": "unbond",
        "inputs": [
            {"name": "policyID", "type": "uint64", "internalType": "uint64"},
            {"name": "amount", "type": "uint256", "internalType": "uint256"},
            {"name": "newMinBalance", "type": "uint256", "internalType": "uint256"}
        ],
        "outputs": [{"name": "unbondBlock", "type": "uint256", "internalType": "uint256"}],
        "stateMutability": "nonpayable"
    },
    {
        "type": "function",
        "name": "unbondingCompleteBlock",
        "inputs": [
            {"name": "policyID", "type": "uint64", "internalType": "uint64"},
            {"name": "account", "type": "address", "internalType": "address"}
        ],
        "outputs": [{"name": "", "type": "uint256", "internalType": "uint256"}],
        "stateMutability": "view"
    },
    {
        "type": "function",
        "name": "withdraw",
        "inputs": [
            {"name": "assets", "type": "uint256", "internalType": "uint256"},
            {"name": "receiver", "type": "address", "internalType": "address"},
            {"name": "owner", "type": "address", "internalType": "address"}
        ],
        "outputs": [{"name": "", "type": "uint256", "internalType": "uint256"}],
        "stateMutability": "nonpayable"
    },
    # Events
    {
        "type": "event",
        "name": "AddPolicyAgent",
        "inputs": [
            {"name": "policyID", "type": "uint64", "indexed": True, "internalType": "uint64"},
            {"name": "agent", "type": "address", "indexed": True, "internalType": "address"}
        ],
        "anonymous": False
    },
    {
        "type": "event",
        "name": "AgentExecuteWithSponsor",
        "inputs": [
            {"name": "policyID", "type": "uint64", "indexed": True, "internalType": "uint64"},
            {"name": "payor", "type": "address", "indexed": True, "internalType": "address"},
            {"name": "agent", "type": "address", "indexed": True, "internalType": "address"},
            {"name": "recipient", "type": "address", "indexed": False, "internalType": "address"},
            {"name": "msgValue", "type": "uint256", "indexed": False, "internalType": "uint256"},
            {"name": "gasLimit", "type": "uint256", "indexed": False, "internalType": "uint256"},
            {"name": "actualPayorCost", "type": "uint256", "indexed": False, "internalType": "uint256"}
        ],
        "anonymous": False
    },
    {
        "type": "event",
        "name": "AgentTransferFromBonded",
        "inputs": [
            {"name": "policyID", "type": "uint64", "indexed": True, "internalType": "uint64"},
            {"name": "from", "type": "address", "indexed": True, "internalType": "address"},
            {"name": "to", "type": "address", "indexed": True, "internalType": "address"},
            {"name": "amount", "type": "uint256", "indexed": False, "internalType": "uint256"}
        ],
        "anonymous": False
    },
    {
        "type": "event",
        "name": "AgentUnbonded",
        "inputs": [
            {"name": "policyID", "type": "uint64", "indexed": True, "internalType": "uint64"},
            {"name": "from", "type": "address", "indexed": True, "internalType": "address"},
            {"name": "amount", "type": "uint256", "indexed": False, "internalType": "uint256"}
        ],
        "anonymous": False
    },
    {
        "type": "event",
        "name": "AgentWithdrawFromBonded",
        "inputs": [
            {"name": "policyID", "type": "uint64", "indexed": True, "internalType": "uint64"},
            {"name": "from", "type": "address", "indexed": True, "internalType": "address"},
            {"name": "to", "type": "address", "indexed": True, "internalType": "address"},
            {"name": "amount", "type": "uint256", "indexed": False, "internalType": "uint256"}
        ],
        "anonymous": False
    },
    {
        "type": "event",
        "name": "Approval",
        "inputs": [
            {"name": "owner", "type": "address", "indexed": True, "internalType": "address"},
            {"name": "spender", "type": "address", "indexed": True, "internalType": "address"},
            {"name": "value", "type": "uint256", "indexed": False, "internalType": "uint256"}
        ],
        "anonymous": False
    },
    {
        "type": "event",
        "name": "Bond",
        "inputs": [
            {"name": "policyID", "type": "uint64", "indexed": True, "internalType": "uint64"},
            {"name": "account", "type": "address", "indexed": True, "internalType": "address"},
            {"name": "amount", "type": "uint256", "indexed": False, "internalType": "uint256"}
        ],
        "anonymous": False
    },
    {
        "type": "event",
        "name": "Claim",
        "inputs": [
            {"name": "policyID", "type": "uint64", "indexed": True, "internalType": "uint64"},
            {"name": "account", "type": "address", "indexed": True, "internalType": "address"},
            {"name": "amount", "type": "uint256", "indexed": False, "internalType": "uint256"}
        ],
        "anonymous": False
    },
    {
        "type": "event",
        "name": "CreatePolicy",
        "inputs": [
            {"name": "policyID", "type": "uint64", "indexed": True, "internalType": "uint64"},
            {"name": "creator", "type": "address", "indexed": True, "internalType": "address"},
            {"name": "escrowDuration", "type": "uint48", "indexed": False, "internalType": "uint48"}
        ],
        "anonymous": False
    },
    {
        "type": "event",
        "name": "Deposit",
        "inputs": [
            {"name": "sender", "type": "address", "indexed": True, "internalType": "address"},
            {"name": "owner", "type": "address", "indexed": True, "internalType": "address"},
            {"name": "assets", "type": "uint256", "indexed": False, "internalType": "uint256"},
            {"name": "shares", "type": "uint256", "indexed": False, "internalType": "uint256"}
        ],
        "anonymous": False
    },
    {
        "type": "event",
        "name": "DisablePolicy",
        "inputs": [{"name": "policyID", "type": "uint64", "indexed": True, "internalType": "uint64"}],
        "anonymous": False
    },
    {
        "type": "event",
        "name": "EIP712DomainChanged",
        "inputs": [],
        "anonymous": False
    },
    {
        "type": "event",
        "name": "Initialized",
        "inputs": [{"name": "version", "type": "uint64", "indexed": False, "internalType": "uint64"}],
        "anonymous": False
    },
    {
        "type": "event",
        "name": "RemovePolicyAgent",
        "inputs": [
            {"name": "policyID", "type": "uint64", "indexed": True, "internalType": "uint64"},
            {"name": "agent", "type": "address", "indexed": True, "internalType": "address"}
        ],
        "anonymous": False
    },
    {
        "type": "event",
        "name": "SetTopUp",
        "inputs": [
            {"name": "policyID", "type": "uint64", "indexed": True, "internalType": "uint64"},
            {"name": "account", "type": "address", "indexed": True, "internalType": "address"},
            {"name": "minBonded", "type": "uint128", "indexed": False, "internalType": "uint128"},
            {"name": "maxTopUpPerPeriod", "type": "uint128", "indexed": False, "internalType": "uint128"},
            {"name": "topUpPeriodDuration", "type": "uint32", "indexed": False, "internalType": "uint32"}
        ],
        "anonymous": False
    },
    {
        "type": "event",
        "name": "Transfer",
        "inputs": [
            {"name": "from", "type": "address", "indexed": True, "internalType": "address"},
            {"name": "to", "type": "address", "indexed": True, "internalType": "address"},
            {"name": "value", "type": "uint256", "indexed": False, "internalType": "uint256"}
        ],
        "anonymous": False
    },
    {
        "type": "event",
        "name": "Unbond",
        "inputs": [
            {"name": "policyID", "type": "uint64", "indexed": True, "internalType": "uint64"},
            {"name": "account", "type": "address", "indexed": True, "internalType": "address"},
            {"name": "amount", "type": "uint256", "indexed": False, "internalType": "uint256"},
            {"name": "expectedUnbondBlock", "type": "uint256", "indexed": False, "internalType": "uint256"}
        ],
        "anonymous": False
    },
    {
        "type": "event",
        "name": "Withdraw",
        "inputs": [
            {"name": "sender", "type": "address", "indexed": True, "internalType": "address"},
            {"name": "receiver", "type": "address", "indexed": True, "internalType": "address"},
            {"name": "owner", "type": "address", "indexed": True, "internalType": "address"},
            {"name": "assets", "type": "uint256", "indexed": False, "internalType": "uint256"},
            {"name": "shares", "type": "uint256", "indexed": False, "internalType": "uint256"}
        ],
        "anonymous": False
    },
    # Errors (included for completeness, though not directly used in Python)
    {"type": "error", "name": "AgentSelfUnbondingDisallowed", "inputs": [{"name": "policyID", "type": "uint64"}, {"name": "agent", "type": "address"}]},
    {"type": "error", "name": "ECDSAInvalidSignature", "inputs": []},
    {"type": "error", "name": "ECDSAInvalidSignatureLength", "inputs": [{"name": "length", "type": "uint256"}]},
    {"type": "error", "name": "ECDSAInvalidSignatureS", "inputs": [{"name": "s", "type": "bytes32"}]},
    {"type": "error", "name": "ERC20InsufficientAllowance", "inputs": [{"name": "spender", "type": "address"}, {"name": "allowance", "type": "uint256"}, {"name": "needed", "type": "uint256"}]},
    {"type": "error", "name": "ERC20InsufficientBalance", "inputs": [{"name": "sender", "type": "address"}, {"name": "balance", "type": "uint256"}, {"name": "needed", "type": "uint256"}]},
    {"type": "error", "name": "ERC20InvalidApprover", "inputs": [{"name": "approver", "type": "address"}]},
    {"type": "error", "name": "ERC20InvalidReceiver", "inputs": [{"name": "receiver", "type": "address"}]},
    {"type": "error", "name": "ERC20InvalidSender", "inputs": [{"name": "sender", "type": "address"}]},
    {"type": "error", "name": "ERC20InvalidSpender", "inputs": [{"name": "spender", "type": "address"}]},
    {"type": "error", "name": "ERC2612ExpiredSignature", "inputs": [{"name": "deadline", "type": "uint256"}]},
    {"type": "error", "name": "ERC2612InvalidSigner", "inputs": [{"name": "signer", "type": "address"}, {"name": "owner", "type": "address"}]},
    {"type": "error", "name": "ERC4626ExceededMaxDeposit", "inputs": [{"name": "receiver", "type": "address"}, {"name": "assets", "type": "uint256"}, {"name": "max", "type": "uint256"}]},
    {"type": "error", "name": "ERC4626ExceededMaxMint", "inputs": [{"name": "receiver", "type": "address"}, {"name": "shares", "type": "uint256"}, {"name": "max", "type": "uint256"}]},
    {"type": "error", "name": "ERC4626ExceededMaxRedeem", "inputs": [{"name": "owner", "type": "address"}, {"name": "shares", "type": "uint256"}, {"name": "max", "type": "uint256"}]},
    {"type": "error", "name": "ERC4626ExceededMaxWithdraw", "inputs": [{"name": "owner", "type": "address"}, {"name": "assets", "type": "uint256"}, {"name": "max", "type": "uint256"}]},
    {"type": "error", "name": "ForwardingError", "inputs": [{"name": "nestedError", "type": "bytes4"}]},
    {"type": "error", "name": "InsufficientBondedForHold", "inputs": [{"name": "bonded", "type": "uint256"}, {"name": "holdRequested", "type": "uint256"}]},
    {"type": "error", "name": "InsufficientFunds", "inputs": [{"name": "bonded", "type": "uint128"}, {"name": "unbonding", "type": "uint128"}, {"name": "held", "type": "uint128"}, {"name": "requested", "type": "uint128"}]},
    {"type": "error", "name": "InsufficientNativeTokenSent", "inputs": []},
    {"type": "error", "name": "InsufficientUnbondedBalance", "inputs": [{"name": "available", "type": "uint256"}, {"name": "requested", "type": "uint256"}]},
    {"type": "error", "name": "InsufficientUnbondingBalance", "inputs": [{"name": "available", "type": "uint256"}, {"name": "requested", "type": "uint256"}]},
    {"type": "error", "name": "InsufficientUnheldBondedBalance", "inputs": [{"name": "bonded", "type": "uint128"}, {"name": "held", "type": "uint128"}, {"name": "requested", "type": "uint128"}]},
    {"type": "error", "name": "InvalidAccountNonce", "inputs": [{"name": "account", "type": "address"}, {"name": "currentNonce", "type": "uint256"}]},
    {"type": "error", "name": "InvalidInitialization", "inputs": []},
    {"type": "error", "name": "MsgDotValueExceedsMsgValueArg", "inputs": [{"name": "msgDotValue", "type": "uint256"}, {"name": "msgValueArg", "type": "uint256"}]},
    {"type": "error", "name": "MsgGasLimitTooLow", "inputs": [{"name": "gasLeft", "type": "uint256"}, {"name": "gasLimit", "type": "uint256"}]},
    {"type": "error", "name": "NotInitializing", "inputs": []},
    {"type": "error", "name": "NotPolicyAgent", "inputs": [{"name": "policyID", "type": "uint64"}, {"name": "caller", "type": "address"}]},
    {"type": "error", "name": "PolicyAgentAlreadyExists", "inputs": [{"name": "policyID", "type": "uint64"}, {"name": "agent", "type": "address"}]},
    {"type": "error", "name": "PolicyAgentNotFound", "inputs": [{"name": "policyID", "type": "uint64"}, {"name": "agent", "type": "address"}]},
    {"type": "error", "name": "PolicyInactive", "inputs": [{"name": "policyID", "type": "uint64"}]},
    {"type": "error", "name": "PolicyNeedsAtLeastOneAgent", "inputs": [{"name": "policyID", "type": "uint64"}]},
    {"type": "error", "name": "SafeCastOverflowedUintDowncast", "inputs": [{"name": "bits", "type": "uint8"}, {"name": "value", "type": "uint256"}]},
    {"type": "error", "name": "TopUpPeriodDurationTooShort", "inputs": [{"name": "requestedPeriodDuration", "type": "uint32"}, {"name": "minPeriodDuration", "type": "uint32"}]},
    {"type": "error", "name": "UnbondingPeriodIncomplete", "inputs": [{"name": "unbondingCompleteBlock", "type": "uint256"}]}
]

# Initialize web3 provider
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Initialize contract
shmonad_contract = w3.eth.contract(address=SHMONAD_ADDRESS, abi=SHMONAD_ABI)

# Display functions
def print_border(text, color=Fore.CYAN, width=60):
    print(f"{color}┌{'─' * (width - 2)}┐{Style.RESET_ALL}")
    print(f"{color}│ {text:^56} │{Style.RESET_ALL}")
    print(f"{color}└{'─' * (width - 2)}┘{Style.RESET_ALL}")

def print_step(step, message, lang):
    steps = {
        'vi': {'deposit': 'Mua shMON', 'stake': 'Stake shMON', 'unstake': 'Unstake shMON', 'redeem': 'Bán shMON'},
        'en': {'deposit': 'Buy shMON', 'stake': 'Stake shMON', 'unstake': 'Unstake shMON', 'redeem': 'Sell shMON'}
    }
    step_text = steps[lang].get(step, step)  # Nếu step không có trong dict, dùng nguyên giá trị
    print(f"{Fore.YELLOW}➤ {Fore.CYAN}{step_text:<15}{Style.RESET_ALL} | {message}")

# Utility functions
def load_private_keys(file_path='pvkey.txt'):
    try:
        with open(file_path, 'r') as file:
            keys = [line.strip() for line in file.readlines() if line.strip()]
            if not keys:
                print(f"{Fore.RED}❌ Không tìm thấy private key hợp lệ trong {file_path}{Style.RESET_ALL}")
            return keys
    except FileNotFoundError:
        print(f"{Fore.RED}❌ Không tìm thấy file {file_path}{Style.RESET_ALL}")
        return []
    except Exception as e:
        print(f"{Fore.RED}❌ Lỗi khi đọc {file_path}: {str(e)}{Style.RESET_ALL}")
        return []

def get_percentage_from_user(language):
    lang = {
        'vi': "Nhập phần trăm sử dụng (1-100, mặc định 20): ",
        'en': "Enter percentage to use (1-100, default 20): "
    }
    error = {
        'vi': "Phần trăm phải từ 1 đến 100 / Nhập lại số hợp lệ!",
        'en': "Percentage must be 1-100 / Enter a valid number!"
    }
    while True:
        try:
            print_border(lang[language], Fore.YELLOW)
            amount = float(input(f"{Fore.GREEN}➤ {Style.RESET_ALL}"))
            if 1 <= amount <= 100:
                return amount
            print(f"{Fore.RED}❌ {error[language]}{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}❌ {error[language]}{Style.RESET_ALL}")
            return 20  # Default value

def get_mon_amount_from_user(language):
    lang = {
        'vi': "Nhập số MON để mua shMON (0.01 - 999): ",
        'en': "Enter MON amount to buy shMON (0.01 - 999): "
    }
    error = {
        'vi': "Số phải từ 0.01 đến 999 / Nhập lại số hợp lệ!",
        'en': "Amount must be 0.01-999 / Enter a valid number!"
    }
    while True:
        try:
            print_border(lang[language], Fore.YELLOW)
            amount = float(input(f"{Fore.GREEN}➤ {Style.RESET_ALL}"))
            if 0.01 <= amount <= 999:
                return w3.to_wei(amount, 'ether')
            print(f"{Fore.RED}❌ {error[language]}{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}❌ {error[language]}{Style.RESET_ALL}")

def get_random_delay(min_delay=10, max_delay=30):
    return random.randint(min_delay, max_delay)

def get_balance(account, token_type='mon'):
    try:
        if token_type == "mon":
            return w3.eth.get_balance(account)
        elif token_type == "shmon":
            return shmonad_contract.functions.balanceOf(account).call()
        elif token_type == "bonded":
            return shmonad_contract.functions.balanceOfBonded(STAKE_POLICY_ID, account).call()
    except Exception as e:
        print(f"{Fore.RED}❌ Lỗi khi lấy số dư {token_type}: {str(e)}{Style.RESET_ALL}")
        return 0

# Core functions
def buy_shmon(private_key, amount, language):
    try:
        account = w3.eth.account.from_key(private_key)
        wallet = account.address[:8] + "..."
        mon_balance = get_balance(account.address, "mon")
        if mon_balance < amount:
            print_step('deposit', f"{Fore.RED}Không đủ MON: {w3.from_wei(mon_balance, 'ether')}{Style.RESET_ALL}", language)
            return False

        lang = {
            'vi': {
                'start': f"Mua {w3.from_wei(amount, 'ether')} shMON với MON | {wallet}",
                'send': 'Đang gửi giao dịch...',
                'success': 'Mua shMON thành công!'
            },
            'en': {
                'start': f"Buy {w3.from_wei(amount, 'ether')} shMON with MON | {wallet}",
                'send': 'Sending transaction...',
                'success': 'Buy shMON successful!'
            }
        }[language]

        print_border(lang['start'])
        tx = shmonad_contract.functions.deposit(amount, account.address).build_transaction({
            'from': account.address,
            'value': amount,
            'gas': 100000,
            'gasPrice': w3.to_wei('50', 'gwei'),
            'nonce': w3.eth.get_transaction_count(account.address),
            'chainId': CHAIN_ID
        })

        print_step('deposit', lang['send'], language)
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        print_step('deposit', f"Tx: {Fore.YELLOW}{EXPLORER_URL}{tx_hash.hex()}{Style.RESET_ALL}", language)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt['status'] == 1:
            print_step('deposit', f"{Fore.GREEN}{lang['success']}{Style.RESET_ALL}", language)
            return True
        else:
            print_step('deposit', f"{Fore.RED}Giao dịch thất bại{Style.RESET_ALL}", language)
            return False
    except Exception as e:
        print_step('deposit', f"{Fore.RED}Lỗi: {str(e)}{Style.RESET_ALL}", language)
        return False

def stake_shmon(private_key, amount, language):
    try:
        account = w3.eth.account.from_key(private_key)
        wallet = account.address[:8] + "..."
        shmon_balance = get_balance(account.address, "shmon")
        if shmon_balance < amount:
            print_step('stake', f"{Fore.RED}Không đủ shMON: {w3.from_wei(shmon_balance, 'ether')}{Style.RESET_ALL}", language)
            return False

        lang = {
            'vi': {
                'start': f"Stake {w3.from_wei(amount, 'ether')} shMON | {wallet}",
                'send': 'Đang gửi giao dịch...',
                'success': 'Stake shMON thành công!'
            },
            'en': {
                'start': f"Stake {w3.from_wei(amount, 'ether')} shMON | {wallet}",
                'send': 'Sending transaction...',
                'success': 'Stake shMON successful!'
            }
        }[language]

        print_border(lang['start'])
        tx = shmonad_contract.functions.bond(STAKE_POLICY_ID, account.address, amount).build_transaction({
            'from': account.address,
            'gas': 100000,
            'gasPrice': w3.to_wei('50', 'gwei'),
            'nonce': w3.eth.get_transaction_count(account.address),
            'chainId': CHAIN_ID
        })

        print_step('stake', lang['send'], language)
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        print_step('stake', f"Tx: {Fore.YELLOW}{EXPLORER_URL}{tx_hash.hex()}{Style.RESET_ALL}", language)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt['status'] == 1:
            print_step('stake', f"{Fore.GREEN}{lang['success']}{Style.RESET_ALL}", language)
            return True
        else:
            print_step('stake', f"{Fore.RED}Giao dịch thất bại{Style.RESET_ALL}", language)
            return False
    except Exception as e:
        print_step('stake', f"{Fore.RED}Lỗi: {str(e)}{Style.RESET_ALL}", language)
        return False

def unstake_shmon(private_key, language):
    try:
        account = w3.eth.account.from_key(private_key)
        wallet = account.address[:8] + "..."
        bonded_balance = get_balance(account.address, "bonded")
        if bonded_balance == 0:
            print_step('unstake', f"{Fore.RED}Không có shMON đã stake{Style.RESET_ALL}", language)
            return False

        lang = {
            'vi': {
                'start': f"Unstake {w3.from_wei(bonded_balance, 'ether')} shMON | {wallet}",
                'send_unbond': 'Đang gửi giao dịch unbond...',
                'send_claim': 'Đang gửi giao dịch claim...',
                'success': 'Unstake shMON thành công!'
            },
            'en': {
                'start': f"Unstake {w3.from_wei(bonded_balance, 'ether')} shMON | {wallet}",
                'send_unbond': 'Sending unbond transaction...',
                'send_claim': 'Sending claim transaction...',
                'success': 'Unstake shMON successful!'
            }
        }[language]

        print_border(lang['start'])
        
        # Unbond transaction
        tx_unbond = shmonad_contract.functions.unbond(STAKE_POLICY_ID, bonded_balance, bonded_balance).build_transaction({
            'from': account.address,
            'gas': 100000,
            'gasPrice': w3.to_wei('50', 'gwei'),
            'nonce': w3.eth.get_transaction_count(account.address),
            'chainId': CHAIN_ID
        })

        print_step('unstake', lang['send_unbond'], language)
        signed_tx_unbond = w3.eth.account.sign_transaction(tx_unbond, private_key)
        tx_hash_unbond = w3.eth.send_raw_transaction(signed_tx_unbond.raw_transaction)
        print_step('unstake', f"Tx Unbond: {Fore.YELLOW}{EXPLORER_URL}{tx_hash_unbond.hex()}{Style.RESET_ALL}", language)
        receipt_unbond = w3.eth.wait_for_transaction_receipt(tx_hash_unbond)
        if receipt_unbond['status'] != 1:
            print_step('unstake', f"{Fore.RED}Unbond thất bại{Style.RESET_ALL}", language)
            return False

        # Wait before claim
        wait_time = random.randint(30, 60)
        print_step('unstake', f"Đợi {wait_time} giây trước khi claim..." if language == 'vi' else f"Waiting {wait_time} seconds before claiming...", language)
        time.sleep(wait_time)

        # Claim transaction
        tx_claim = shmonad_contract.functions.claim(STAKE_POLICY_ID, bonded_balance).build_transaction({
            'from': account.address,
            'gas': 100000,
            'gasPrice': w3.to_wei('50', 'gwei'),
            'nonce': w3.eth.get_transaction_count(account.address),
            'chainId': CHAIN_ID
        })

        print_step('unstake', lang['send_claim'], language)
        signed_tx_claim = w3.eth.account.sign_transaction(tx_claim, private_key)
        tx_hash_claim = w3.eth.send_raw_transaction(signed_tx_claim.raw_transaction)
        print_step('unstake', f"Tx Claim: {Fore.YELLOW}{EXPLORER_URL}{tx_hash_claim.hex()}{Style.RESET_ALL}", language)
        receipt_claim = w3.eth.wait_for_transaction_receipt(tx_hash_claim)
        if receipt_claim['status'] == 1:
            print_step('unstake', f"{Fore.GREEN}{lang['success']}{Style.RESET_ALL}", language)
            return True
        else:
            print_step('unstake', f"{Fore.RED}Claim thất bại{Style.RESET_ALL}", language)
            return False
    except Exception as e:
        print_step('unstake', f"{Fore.RED}Lỗi: {str(e)}{Style.RESET_ALL}", language)
        return False

def sell_shmon(private_key, amount, language):
    try:
        account = w3.eth.account.from_key(private_key)
        wallet = account.address[:8] + "..."
        shmon_balance = get_balance(account.address, "shmon")
        if shmon_balance < amount:
            print_step('redeem', f"{Fore.RED}Không đủ shMON: {w3.from_wei(shmon_balance, 'ether')}{Style.RESET_ALL}", language)
            return False

        lang = {
            'vi': {
                'start': f"Bán {w3.from_wei(amount, 'ether')} shMON | {wallet}",
                'send': 'Đang gửi giao dịch...',
                'success': 'Bán shMON thành công!'
            },
            'en': {
                'start': f"Sell {w3.from_wei(amount, 'ether')} shMON | {wallet}",
                'send': 'Sending transaction...',
                'success': 'Sell shMON successful!'
            }
        }[language]

        print_border(lang['start'])
        tx = shmonad_contract.functions.redeem(amount, account.address, account.address).build_transaction({
            'from': account.address,
            'gas': 100000,
            'gasPrice': w3.to_wei('50', 'gwei'),
            'nonce': w3.eth.get_transaction_count(account.address),
            'chainId': CHAIN_ID
        })

        print_step('redeem', lang['send'], language)
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        print_step('redeem', f"Tx: {Fore.YELLOW}{EXPLORER_URL}{tx_hash.hex()}{Style.RESET_ALL}", language)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt['status'] == 1:
            print_step('redeem', f"{Fore.GREEN}{lang['success']}{Style.RESET_ALL}", language)
            return True
        else:
            print_step('redeem', f"{Fore.RED}Giao dịch thất bại{Style.RESET_ALL}", language)
            return False
    except Exception as e:
        print_step('redeem', f"{Fore.RED}Lỗi: {str(e)}{Style.RESET_ALL}", language)
        return False

# Main execution
def run_swap_cycle(cycles, private_keys, language, percentage):
    for cycle in range(1, cycles + 1):
        for pk in private_keys:
            account = w3.eth.account.from_key(pk)
            wallet = account.address[:8] + "..."
            msg = f"CYCLE {cycle}/{cycles} | Tài khoản / Account: {wallet}"
            print(f"{Fore.CYAN}{'═' * 60}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}│ {msg:^56} │{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'═' * 60}{Style.RESET_ALL}")

            shmon_balance = get_balance(account.address, "shmon")
            bonded_balance = get_balance(account.address, "bonded")
            mon_balance = get_balance(account.address, "mon")

            print(f"{Fore.YELLOW}Số dư: MON: {w3.from_wei(mon_balance, 'ether'):.6f}, shMON: {w3.from_wei(shmon_balance, 'ether'):.6f}, Bonded shMON: {w3.from_wei(bonded_balance, 'ether'):.6f}{Style.RESET_ALL}")

            mon_balance = get_balance(account.address, "mon")
            # Simpan 0.01 MON untuk gas
            gas_reserve = w3.to_wei(0.01, 'ether')
            available_balance = max(0, mon_balance - gas_reserve)
            amount = int(available_balance * percentage / 100)

            # Logic: Buy -> Stake -> Unstake -> Sell
            if mon_balance > amount and buy_shmon(pk, amount, language):
                time.sleep(5)
                shmon_balance = get_balance(account.address, "shmon")
                if shmon_balance > 0 and stake_shmon(pk, shmon_balance, language):
                    time.sleep(5)
                    if bonded_balance > 0 and unstake_shmon(pk, language):
                        time.sleep(5)
                        shmon_balance = get_balance(account.address, "shmon")
                        if shmon_balance > 0:
                            sell_shmon(pk, shmon_balance, language)

            if cycle < cycles or pk != private_keys[-1]:
                delay = get_random_delay()
                wait_msg = f"Đợi {delay} giây..." if language == 'vi' else f"Waiting {delay} seconds..."
                print(f"\n{Fore.YELLOW}⏳ {wait_msg}{Style.RESET_ALL}")
                time.sleep(delay)

def run(language='vi'):
    print(f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}│ {'SHMONAD - MONAD TESTNET':^56} │{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{'═' * 60}{Style.RESET_ALL}")

    private_keys = load_private_keys()
    if not private_keys:
        print(f"{Fore.RED}Không có private key nào được tải, thoát chương trình{Style.RESET_ALL}")
        return

    print(f"{Fore.CYAN}👥 {'Tài khoản' if language == 'vi' else 'Accounts'}: {len(private_keys)}{Style.RESET_ALL}")
    
    # Lấy persentase sử dụng
    percentage = get_percentage_from_user(language)
    while True:
        try:
            print_border("SỐ VÒNG LẶP / NUMBER OF CYCLES", Fore.YELLOW)
            cycles = input(f"{Fore.GREEN}➤ {'Nhập số (mặc định 1): ' if language == 'vi' else 'Enter number (default 1): '}{Style.RESET_ALL}")
            cycles = int(cycles) if cycles else 1
            if cycles > 0:
                break
            print(f"{Fore.RED}❌ Số phải lớn hơn 0 / Number must be > 0{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}❌ Nhập số hợp lệ / Enter a valid number{Style.RESET_ALL}")

    start_msg = f"Chạy {cycles} vòng shMON..." if language == 'vi' else f"Running {cycles} shMON cycles..."
    print(f"{Fore.YELLOW}🚀 {start_msg}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}💹 {'Phần trăm sử dụng' if language == 'vi' else 'Usage percentage'}: {percentage}%{Style.RESET_ALL}")
    run_swap_cycle(cycles, private_keys, language, percentage)

if __name__ == "__main__":
    run('en')
