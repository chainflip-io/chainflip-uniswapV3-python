from .utilities import *
from ..src.libraries.Account import Account, Ledger


def test_tokenTransfer():
    account0 = ["ALICE", TEST_TOKENS, [100, 100]]
    account1 = ["BOB", TEST_TOKENS, [100, 100]]

    ledger = Ledger([account0, account1])
    accounts = list(ledger.accounts.keys())

    # Token Transfer Test
    assert ledger.balanceOf(accounts[0], TEST_TOKENS[0]) == 100
    assert ledger.balanceOf(accounts[0], TEST_TOKENS[1]) == 100
    assert ledger.balanceOf(accounts[1], TEST_TOKENS[0]) == 100
    assert ledger.balanceOf(accounts[1], TEST_TOKENS[1]) == 100

    ledger.transferToken(accounts[0], accounts[1], TEST_TOKENS[0], 25)

    assert ledger.balanceOf(accounts[0], TEST_TOKENS[0]) == 75
    assert ledger.balanceOf(accounts[0], TEST_TOKENS[1]) == 100
    assert ledger.balanceOf(accounts[1], TEST_TOKENS[0]) == 125
    assert ledger.balanceOf(accounts[1], TEST_TOKENS[1]) == 100

    # Negative Amount
    tryExceptHandler(
        ledger.transferToken,
        "OF or UF of UINT256",
        accounts[0],
        accounts[1],
        TEST_TOKENS[0],
        -25,
    )
    tryExceptHandler(
        ledger.transferToken,
        "OF or UF of UINT256",
        accounts[0],
        accounts[1],
        TEST_TOKENS[1],
        -25,
    )

    # Insufficient Balance
    tryExceptHandler(
        ledger.transferToken,
        "Insufficient balance",
        accounts[0],
        accounts[1],
        TEST_TOKENS[0],
        150,
    )


def test_tokenReceive():
    account0 = ["ALICE", TEST_TOKENS, [100, 100]]

    ledger = Ledger([account0])
    accounts = list(ledger.accounts.keys())

    ledger.receiveToken(accounts[0], TEST_TOKENS[0], 25)

    assert ledger.balanceOf(accounts[0], TEST_TOKENS[0]) == 125
    assert ledger.balanceOf(accounts[0], TEST_TOKENS[1]) == 100

    ledger.receiveToken(accounts[0], TEST_TOKENS[0], 0)
    assert ledger.balanceOf(accounts[0], TEST_TOKENS[0]) == 125
    assert ledger.balanceOf(accounts[0], TEST_TOKENS[1]) == 100

    ledger.receiveToken(accounts[0], TEST_TOKENS[1], 13)
    assert ledger.balanceOf(accounts[0], TEST_TOKENS[0]) == 125
    assert ledger.balanceOf(accounts[0], TEST_TOKENS[1]) == 113

    tryExceptHandler(
        ledger.receiveToken, "OF or UF of UINT256", accounts[0], TEST_TOKENS[0], -25
    )
    tryExceptHandler(
        ledger.receiveToken, "OF or UF of UINT256", accounts[0], TEST_TOKENS[1], -25
    )
