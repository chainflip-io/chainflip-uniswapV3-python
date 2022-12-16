from ..src.UniswapPool import *
from ..src.libraries import Tick
from .utilities import *


# tickSpacingToMaxLiquidityPerTick


def test_returns_lowFee():
    print("returns the correct value for low fee")
    maxLiquidityPerTick = Tick.tickSpacingToMaxLiquidityPerTick(
        TICK_SPACINGS[FeeAmount.LOW]
    )
    assert maxLiquidityPerTick == 1917569901783203986719870431555990  ##0.8 bits
    assert maxLiquidityPerTick == getMaxLiquidityPerTick(TICK_SPACINGS[FeeAmount.LOW])


def test_returns_mediumFee():
    print("returns the correct value for medium fee")
    maxLiquidityPerTick = Tick.tickSpacingToMaxLiquidityPerTick(
        TICK_SPACINGS[FeeAmount.MEDIUM]
    )
    assert maxLiquidityPerTick == 11505743598341114571880798222544994  ## 113.1 bits
    assert maxLiquidityPerTick == getMaxLiquidityPerTick(
        TICK_SPACINGS[FeeAmount.MEDIUM]
    )


def test_returns_highFee():
    print("returns the correct value for high fee")
    maxLiquidityPerTick = Tick.tickSpacingToMaxLiquidityPerTick(
        TICK_SPACINGS[FeeAmount.HIGH]
    )
    assert maxLiquidityPerTick == 38350317471085141830651933667504588  ## 114.7 bits
    assert maxLiquidityPerTick == getMaxLiquidityPerTick(TICK_SPACINGS[FeeAmount.HIGH])


def tests_returns_allRange():
    print("returns the correct value for entire range")
    maxLiquidityPerTick = Tick.tickSpacingToMaxLiquidityPerTick(887272)
    assert maxLiquidityPerTick == MAX_UINT128 // 3  ## 126 bits
    assert maxLiquidityPerTick == getMaxLiquidityPerTick(887272)


def test_returns_for2302():
    print("returns the correct value for 2302")
    maxLiquidityPerTick = Tick.tickSpacingToMaxLiquidityPerTick(2302)
    assert maxLiquidityPerTick == 441351967472034323558203122479595605  ## 118 bits
    assert maxLiquidityPerTick == getMaxLiquidityPerTick(2302)


# getFreeGrowthInside


def test_returns_all_twoUninitialized_ifInside():
    print("returns all for two uninitialized ticks if tick is inside")
    tickMapping = {}
    insertUninitializedTickstoMapping(tickMapping, [-2, 2, 0, 15, 1])
    (feeGrowthInside0X128, feeGrowthInside1X128) = Tick.getFeeGrowthInside(
        tickMapping, -2, 2, 0, 15, 15
    )
    assert feeGrowthInside0X128 == 15
    assert feeGrowthInside1X128 == 15


def test_returns_0_twoUninitialized_ifAbove():
    print("returns 0 for two uninitialized ticks if tick is above")
    tickMapping = {}
    print(tickMapping)
    insertUninitializedTickstoMapping(tickMapping, [-2, 2, 4, 15])
    (feeGrowthInside0X128, feeGrowthInside1X128) = Tick.getFeeGrowthInside(
        tickMapping, -2, 2, 4, 15, 15
    )
    assert feeGrowthInside0X128 == 0
    assert feeGrowthInside1X128 == 0


def test_returns_0_twoUninitialized_ifBelow():
    print("returns 0 for two uninitialized ticks if tick is below")
    tickMapping = {}
    insertUninitializedTickstoMapping(tickMapping, [-2, 2, -4, 15])
    (feeGrowthInside0X128, feeGrowthInside1X128) = Tick.getFeeGrowthInside(
        tickMapping, -2, 2, -4, 15, 15
    )
    assert feeGrowthInside0X128 == 0
    assert feeGrowthInside1X128 == 0


def test_substractUpperTick_ifBelow():
    print("subtracts upper tick if below")
    tickMapping = {}
    insertInitializedTicksToMapping(tickMapping, [2], [TickInfo(0, 0, 2, 3)])
    insertUninitializedTickstoMapping(tickMapping, [-2, 0, 15])
    (feeGrowthInside0X128, feeGrowthInside1X128) = Tick.getFeeGrowthInside(
        tickMapping, -2, 2, 0, 15, 15
    )
    assert feeGrowthInside0X128 == 13
    assert feeGrowthInside1X128 == 12


def test_substractLowerTick_ifAbove():
    print("subtracts lower tick if above")
    tickMapping = {}
    insertInitializedTicksToMapping(tickMapping, [-2], [TickInfo(0, 0, 2, 3)])
    insertUninitializedTickstoMapping(tickMapping, [2, 0, 15])
    (feeGrowthInside0X128, feeGrowthInside1X128) = Tick.getFeeGrowthInside(
        tickMapping, -2, 2, 0, 15, 15
    )
    assert feeGrowthInside0X128 == 13
    assert feeGrowthInside1X128 == 12


def test_substractUpperAndLower_ifInside():
    print("subtracts upper and lower tick if inside")
    tickMapping = {}
    insertInitializedTicksToMapping(
        tickMapping, [-2, 2], [TickInfo(0, 0, 2, 3), TickInfo(0, 0, 4, 1)]
    )
    insertUninitializedTickstoMapping(tickMapping, [0, 15])
    (feeGrowthInside0X128, feeGrowthInside1X128) = Tick.getFeeGrowthInside(
        tickMapping, -2, 2, 0, 15, 15
    )
    assert feeGrowthInside0X128 == 9
    assert feeGrowthInside1X128 == 11


def test_overflow_insideTick():
    print("works correctly with overflow inside tick")
    tickMapping = {}
    insertInitializedTicksToMapping(
        tickMapping,
        [-2, 2],
        [TickInfo(0, 0, MAX_UINT256 - 3, MAX_UINT256 - 2), TickInfo(0, 0, 3, 5)],
    )
    insertUninitializedTickstoMapping(tickMapping, [0, 15])
    (feeGrowthInside0X128, feeGrowthInside1X128) = Tick.getFeeGrowthInside(
        tickMapping, -2, 2, 0, 15, 15
    )
    assert feeGrowthInside0X128 == 16
    assert feeGrowthInside1X128 == 13


# update

# Ticks.update will create a new tick if the tick is not in the mapping and liquidityDelta > 0
def test_flip_zero_to_nonZero():
    print("flips from zero to non zero")
    assert Tick.update({}, 0, 0, 1, 0, 0, False, 3) == True


def test_noFlip_nonZero_to_gtNonZero():
    print("does not flip from non zero to greater than non zero")
    tickMapping = {}
    Tick.update(tickMapping, 0, 0, 1, 0, 0, False, 3)
    assert Tick.update(tickMapping, 0, 0, 1, 0, 0, False, 3) == False


def test_flip_nonZero_to_zero():
    print("flips from non zero to zero")
    tickMapping = {}
    Tick.update(tickMapping, 0, 0, 1, 0, 0, False, 3)
    assert Tick.update(tickMapping, 0, 0, -1, 0, 0, False, 3) == True


def test_noFlip_nonZero_to_ltNonZero():
    print("does not flip from non zero to lesser nonzero")
    tickMapping = {}
    Tick.update(tickMapping, 0, 0, 2, 0, 0, False, 3)
    assert Tick.update(tickMapping, 0, 0, -1, 0, 0, False, 3) == False

    tickMapping = {}
    Tick.update(tickMapping, 0, 0, 2, 0, 0, False, 3)
    assert Tick.update(tickMapping, 0, 0, -1, 0, 0, False, 3) == False


def test_reverts_totalLiquidityGross_gtMax():
    print("reverts if total liquidity gross is greater than max")
    tickMapping = {}
    Tick.update(tickMapping, 0, 0, 2, 0, 0, False, 3)
    Tick.update(tickMapping, 0, 0, 1, 0, 0, True, 3)
    tryExceptHandler(Tick.update, "LO", tickMapping, 0, 0, 1, 0, 0, False, 3)


def test_liquidity_upperFlag():
    print("nets the liquidity based on upper flag")
    tickMapping = {}
    Tick.update(tickMapping, 0, 0, 2, 0, 0, False, 10)
    Tick.update(tickMapping, 0, 0, 1, 0, 0, True, 10)
    Tick.update(tickMapping, 0, 0, 3, 0, 0, True, 10)
    Tick.update(tickMapping, 0, 0, 1, 0, 0, False, 10)

    assert tickMapping[0].liquidityGross == 2 + 1 + 3 + 1
    assert tickMapping[0].liquidityNet == 2 - 1 - 3 + 1


def test_reverts_overflow_liquidityGross():
    print("reverts on overflow liquidity gross")
    tickMapping = {}
    Tick.update(tickMapping, 0, 0, (MAX_UINT128 // 2) - 1, 0, 0, False, MAX_UINT128)
    tryExceptHandler(
        Tick.update,
        "OF or UF of INT128",
        tickMapping,
        0,
        0,
        (MAX_UINT128 // 2) - 1,
        0,
        0,
        False,
        MAX_UINT128,
    )


def test_growthBelowTicks_lteCurrentTick():
    print("assumes all growth happens below ticks lte current tick")
    tickMapping = {}
    Tick.update(tickMapping, 1, 1, 1, 1, 2, False, MAX_UINT128)

    assert tickMapping.__contains__(1)
    assert tickMapping[1].feeGrowthOutside0X128 == 1
    assert tickMapping[1].feeGrowthOutside1X128 == 2


def test_noGrowth_ifTickInitialized():
    print("does not set any growth fields if tick is already initialized")
    tickMapping = {}
    Tick.update(tickMapping, 1, 1, 1, 1, 2, False, MAX_UINT128)
    Tick.update(tickMapping, 1, 1, 1, 6, 7, False, MAX_UINT128)

    assert tickMapping.__contains__(1)
    assert tickMapping[1].feeGrowthOutside0X128 == 1
    assert tickMapping[1].feeGrowthOutside1X128 == 2


def test_noGrowing_ifTickGtCurrentTick():
    print("does not set any growth fields for ticks gt current tick")
    tickMapping = {}
    Tick.update(tickMapping, 2, 1, 1, 1, 2, False, MAX_UINT128)

    assert tickMapping.__contains__(2)
    assert tickMapping[2].feeGrowthOutside0X128 == 0
    assert tickMapping[2].feeGrowthOutside1X128 == 0


# Clear


def test_deletesAllTickData():
    print("deletes all the data in the tick")
    tickMapping = {2: TickInfo(3, 4, 1, 2)}
    Tick.clear(tickMapping, 2)

    assert not tickMapping.__contains__(2)


# Cross


def test_flip_growthVariables():
    print("flips growth variables")
    tickMapping = {2: TickInfo(3, 4, 1, 2)}
    Tick.cross(tickMapping, 2, 7, 9)

    assert tickMapping.__contains__(2)
    assert tickMapping[2].feeGrowthOutside0X128 == 6
    assert tickMapping[2].feeGrowthOutside1X128 == 7


def test_twoFlips_noOp():
    print("two flips are no op")
    tickMapping = {2: TickInfo(3, 4, 1, 2)}

    Tick.cross(tickMapping, 2, 7, 9)
    Tick.cross(tickMapping, 2, 7, 9)

    assert tickMapping.__contains__(2)
    assert tickMapping[2].feeGrowthOutside0X128 == 1
    assert tickMapping[2].feeGrowthOutside1X128 == 2
