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
    END_TURN = 8
    SETUP_BUILD = 9


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

class DevCardsTypes(Enum):
    KNIGHT = 0
    VICTORY_CARD = 1
    MONOPOLY = 2
    YEAR_OF_PLENTY = 3
    ROAD_BUILDING = 4

class Cost(Enum):
    ROAD = [1, 1, 0, 0, 0]
    SETTLEMENT = [1, 1, 1, 1, 0]
    CITY = [0, 0, 0, 2, 3]
    DEVCARD = [0, 0, 1, 1, 1]

class Resource(Enum):
    WOOD = 0
    BRICK = 1
    SHEEP = 2
    WHEAT = 3
    ORE = 4

class PieceType(Enum):
    SETTLEMENT = 1
    CITY = 2

class BuildingType(Enum):
    ROAD = 0
    SETTLEMENT = 1
    CITY = 2