from .test_uniswapPool import ledger

from ..src.libraries.Factory import *
from .utilities import *

TEST_ADDRESSES = [
    "0x1000000000000000000000000000000000000000",
    "0x2000000000000000000000000000000000000000",
]


def test_initial_fees():
    print("initial enabled fee amounts")
    factory = Factory()
    assert factory.feeAmountTickSpacing[FeeAmount.LOW] == TICK_SPACINGS[FeeAmount.LOW]
    assert (
        factory.feeAmountTickSpacing[FeeAmount.MEDIUM]
        == TICK_SPACINGS[FeeAmount.MEDIUM]
    )
    assert factory.feeAmountTickSpacing[FeeAmount.HIGH] == TICK_SPACINGS[FeeAmount.HIGH]


def createAndCheck_pool(factory, tokens, feeAmount, tickSpacing, ledger):
    print("create and check pool")

    pool = factory.createPool(tokens[0], tokens[1], feeAmount, ledger)

    tryExceptHandler(
        factory.createPool,
        "Pool already exists",
        tokens[0],
        tokens[1],
        feeAmount,
        ledger,
    )
    tryExceptHandler(
        factory.createPool,
        "Pool already exists",
        tokens[1],
        tokens[0],
        feeAmount,
        ledger,
    )

    assert pool.token0 == TEST_ADDRESSES[0], "pool token0"
    assert pool.token1 == TEST_ADDRESSES[1], "pool token1"
    assert pool.fee == feeAmount, "pool fee"
    assert pool.tickSpacing == tickSpacing, "pool tick spacing"


# createPool
def test_lowFeePool(ledger):
    print("succeds for low fee pool")
    createAndCheck_pool(
        Factory(), TEST_ADDRESSES, FeeAmount.LOW, TICK_SPACINGS[FeeAmount.LOW], ledger
    )


def test_mediumFeePool(ledger):
    print("succeds for medium fee pool")
    createAndCheck_pool(
        Factory(),
        TEST_ADDRESSES,
        FeeAmount.MEDIUM,
        TICK_SPACINGS[FeeAmount.MEDIUM],
        ledger,
    )


def test_highFeePool(ledger):
    print("succeds for high fee pool")
    createAndCheck_pool(
        Factory(), TEST_ADDRESSES, FeeAmount.HIGH, TICK_SPACINGS[FeeAmount.HIGH], ledger
    )


def test_tokensReverse(ledger):
    print("succeds for tokens in reverse order")
    createAndCheck_pool(
        Factory(),
        TEST_ADDRESSES[::-1],
        FeeAmount.MEDIUM,
        TICK_SPACINGS[FeeAmount.MEDIUM],
        ledger,
    )


def test_fails_tokenAequalB(ledger):
    print("fails if token a is 0 or token b is 0")
    tryExceptHandler(
        Factory().createPool, "", TEST_ADDRESSES[0], "0", FeeAmount.LOW, ledger
    )
    tryExceptHandler(
        Factory().createPool, "", "0", TEST_ADDRESSES[0], FeeAmount.LOW, ledger
    )
    tryExceptHandler(Factory().createPool, "", "0", "0", FeeAmount.LOW, ledger)


def test_fails_feeAmountNotEnabled(ledger):
    print("fails if fee amount is not enabled")
    tryExceptHandler(
        Factory().createPool,
        "Fee amount not supported",
        TEST_ADDRESSES[0],
        TEST_ADDRESSES[1],
        250,
        ledger,
    )


# setO
def test_fails_feeTooGreat():
    print("fails if fee is too great")
    tryExceptHandler(Factory().enableFeeAmount, "", 1000000, 10)


def test_fails_tickSpacingTooSmall():
    print("fails if tick spacing is too small")
    tryExceptHandler(Factory().enableFeeAmount, "", 500, 0)


def test_fails_tickSpacingTooLarge():
    print("fails if tick spacing is too large")
    tryExceptHandler(Factory().enableFeeAmount, "", 500, 16834)


def test_fails_alreadyInitialized():
    print("fails if already initialized")
    factory = Factory()
    factory.enableFeeAmount(100, 5)
    tryExceptHandler(Factory().enableFeeAmount, "", 100, 0)


def test_setFee():
    print("sets the fee amount in the mapping")
    factory = Factory()
    factory.enableFeeAmount(100, 5)
    assert factory.feeAmountTickSpacing[100] == 5


def test_enablePoolCreation(ledger):
    factory = Factory()
    factory.enableFeeAmount(250, 15)
    createAndCheck_pool(factory, TEST_ADDRESSES, 250, 15, ledger)
