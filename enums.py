from enum import Enum

class ActionType(Enum):
    TRADE = 0 
    BUY_DEV_CARD = 1
    BUILD_ROAD = 2
    BUILD_SETTLEMENT = 3
    BUILD_CITY = 4
    OPEN_DEV_CARD = 5
    MOVE_ROBBER = 6
    ROLL_DICE = 7


class HexType(Enum):
    FOREST = 1
    PASTURE = 2
    FIELD = 3
    HILL = 4
    MOUNTAIN = 5
    DESERT = 6

class HarborType(Enum):
    WOOD = 1
    SHEEP = 2
    WHEAT = 3
    BRICK = 4
    ORE = 5
    ANY3 = 6

class Resource(IntEnum):
    WOOD = 0
    BRICK = 1
    SHEEP = 2
    WHEAT = 3
    ORE = 4

class PieceType(Enum):
    SETTLEMENT = 1
    CITY = 2