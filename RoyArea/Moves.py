from enum import IntEnum
from typing import List, Union
from Hand import Hand
import GameConstants as Consts


class MoveType(IntEnum):
    TRADE = 1
    BUY_DEV = 2
    USE_DEV = 3
    BUILD = 4
    THROW = 5
    PASS = 6


class Move:
    def __init__(self, player_id: int, mtype: MoveType):
        self.__id = player_id
        self.__type = mtype

    def player_id(self) -> int:
        """:returns the id of the player making the move"""
        return self.__id
    
    def get_type(self) -> MoveType:
        """:returns the type of move as a MoveType enum"""
        return self.__type

    def info(self) -> str:
        return f'[MOVE] player = {self.player_id()}, type = {self.get_type().name}'

    def __str__(self) -> str:
        return str(self.__type)


class TradeMove(Move):
    def __init__(self, player_id: int, cards_out: Hand, cards_in: Hand):
        super().__init__(player_id, MoveType.TRADE)
        self.__cards_out = cards_out
        self.__cards_in = cards_in

    def gives(self) -> Hand:
        """:returns cards to be given away by the player (as a Hand object)"""
        return self.__cards_out

    def gets(self) -> Hand:
        """:returns cards to be obtained by the player (as a Hand object)"""
        return self.__cards_in

    def info(self) -> str:
        return f'[MOVE] player_id = {self.player_id()}, type = {self.get_type().name}, gives = {self.gives()}, gets = {self.gets()}'


class BuyDevMove(Move):
    def __init__(self, player_id: int):
        super().__init__(player_id, MoveType.BUY_DEV)

    def info(self) -> str:
        return f'[MOVE] player_id = {self.player_id()}, type = {self.get_type().name}'


class UseDevMove(Move):
    def __init__(self, player_id: int, dtype: Consts.DevType):
        super().__init__(player_id, MoveType.USE_DEV)
        self.__dev_to_use = dtype

    def uses(self) -> Consts.DevType:
        """:returns the dev card to be used as a DevType enum"""
        return self.__dev_to_use

    def info(self) -> str:
        return f'[MOVE] player_id = {self.player_id()}, type = {self.get_type().name}, uses = {self.uses().name}'


class UseRoadBuildingDevMove(UseDevMove):
    def __init__(self, player_id: int, *locs: int):
        super().__init__(player_id, Consts.DevType.ROAD_BUILDING)
        self.__locs = [l for l in locs]
        # assert len(locs) == Consts.ROAD_BUILDING_NUM_ROADS

    def edges(self) -> List[int]:
        return self.__locs


class UseYopDevMove(UseDevMove):
    def __init__(self, player_id: int, *resources: Consts.ResourceType):
        super().__init__(player_id, Consts.DevType.YEAR_OF_PLENTY)
        self.__resources = Hand(*resources)
        assert len(resources) == Consts.YOP_NUM_RESOURCES

    def resources(self) -> Hand:
        return self.__resources


class UseMonopolyDevMove(UseDevMove):
    def __init__(self, player_id: int, resource: Consts.ResourceType):
        super().__init__(player_id, Consts.DevType.MONOPOLY)
        self.__resource = resource

    def resource(self) -> Consts.ResourceType:
        return self.__resource


class UseKnightDevMove(UseDevMove):
    def __init__(self, player_id: int, hex_id: int, opp_id: Union[int, None]):
        super().__init__(player_id, Consts.DevType.KNIGHT)
        self.__hex_id = hex_id
        self.__opp_id = opp_id

    def hex_id(self) -> int:
        return self.__hex_id

    def take_from(self) -> Union[int, None]:
        return self.__opp_id


class ThrowMove(Move):
    def __init__(self, player_id: int, hand: Hand):
        super().__init__(player_id, MoveType.THROW)
        self.__hand = hand

    def throws(self) -> Hand:
        return self.__hand


class BuildMove(Move):
    def __init__(self, player_id: int, btype: Consts.PurchasableType, location: int):
        super().__init__(player_id, MoveType.BUILD)
        self.__to_build = btype
        self.__loc = location

    def builds(self) -> Consts.PurchasableType:
        """:returns the building type as a PurchasableType enum"""
        return self.__to_build

    def at(self) -> int:
        """:returns int value of node / edge idx of location to build on the board (see HexGrid)"""
        return self.__loc

    def info(self) -> str:
        return f'[MOVE] player_id = {self.player_id()}, type = {self.get_type().name}, builds = {self.builds().name}, at = {hex(self.at())}'
