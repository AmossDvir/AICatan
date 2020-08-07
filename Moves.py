from __future__ import annotations
from enum import IntEnum
from typing import List, Union
# from Hand.Hand import Hand.Hand
import Hand
import Player
import GameConstants as Consts


class MoveType(IntEnum):
    TRADE = 1
    BUY_DEV = 2
    USE_DEV = 3
    BUILD = 4
    THROW = 5
    PASS = 6


class Move:
    def __init__(self, player: Player.Player, mtype: MoveType):
        self.__player = player
        self.__type = mtype

    def set_player(self, player: Player.Player) -> None:
        self.__player = player

    def player(self) -> Player.Player:
        """:returns the id of the player making the move"""
        return self.__player
    
    def get_type(self) -> MoveType:
        """:returns the type of move as a MoveType enum"""
        return self.__type

    def info(self) -> str:
        return f'[MOVE] player = {self.player()}, type = {self.get_type().name}'

    def __str__(self) -> str:
        return str(self.__type)


class TradeMove(Move):
    def __init__(self, player: Player.Player, cards_out: Hand.Hand, cards_in: Hand.Hand):
        super().__init__(player, MoveType.TRADE)
        self.__cards_out = cards_out
        self.__cards_in = cards_in

    def gives(self) -> Hand.Hand:
        """:returns cards to be given away by the player (as a Hand.Hand object)"""
        return self.__cards_out

    def gets(self) -> Hand.Hand:
        """:returns cards to be obtained by the player (as a Hand.Hand object)"""
        return self.__cards_in

    def info(self) -> str:
        return f'[MOVE] player = {self.player()}, ' \
               f'type = {self.get_type().name}, gives = {self.gives()}, gets = {self.gets()}'


class BuyDevMove(Move):
    def __init__(self, player: Player.Player):
        super().__init__(player, MoveType.BUY_DEV)

    def info(self) -> str:
        return f'[MOVE] player = {self.player()}, type = {self.get_type().name}'


class UseDevMove(Move):
    def __init__(self, player: Player.Player, dtype: Consts.DevType):
        super().__init__(player, MoveType.USE_DEV)
        self.__dev_to_use = dtype

    def uses(self) -> Consts.DevType:
        """:returns the dev card to be used as a DevType enum"""
        return self.__dev_to_use

    def info(self) -> str:
        return f'[MOVE] player = {self.player()}, type = {self.get_type().name}, uses = {self.uses().name}'


class UseRoadBuildingDevMove(UseDevMove):
    def __init__(self, player: Player.Player, *locs: int):
        super().__init__(player, Consts.DevType.ROAD_BUILDING)
        self.__locs = [loc for loc in locs]
        # assert len(locs) == Consts.ROAD_BUILDING_NUM_ROADS

    def edges(self) -> List[int]:
        return self.__locs


class UseYopDevMove(UseDevMove):
    def __init__(self, player: Player.Player, *resources: Consts.ResourceType):
        super().__init__(player, Consts.DevType.YEAR_OF_PLENTY)
        self.__resources = Hand.Hand(*resources)
        assert len(resources) == Consts.YOP_NUM_RESOURCES

    def resources(self) -> Hand.Hand:
        return self.__resources


class UseMonopolyDevMove(UseDevMove):
    def __init__(self, player: Player.Player, resource: Consts.ResourceType):
        super().__init__(player, Consts.DevType.MONOPOLY)
        self.__resource = resource

    def resource(self) -> Consts.ResourceType:
        return self.__resource


class UseKnightDevMove(UseDevMove):
    def __init__(self, player: Player.Player, hex_id: int, opp: Union[Player.Player, None],
                 robber_activated: bool = False):
        super().__init__(player, Consts.DevType.KNIGHT)
        self.__hex_id = hex_id
        self.__opp = opp
        self.__robber = robber_activated

    def robber_activated(self) -> bool:
        return self.__robber

    def hex_id(self) -> int:
        return self.__hex_id

    def take_from(self) -> Union[Player.Player, None]:
        return self.__opp

    def info(self) -> str:
        return f'[MOVE] player = {self.player()}, ' \
               f'type = {self.get_type().name}, places robber at hex = {self.hex_id()}, takes card from = {self.take_from()}'


class ThrowMove(Move):
    def __init__(self, player: Player.Player, hand: Hand.Hand):
        super().__init__(player, MoveType.THROW)
        self.__hand = hand

    def throws(self) -> Hand.Hand:
        return self.__hand


class BuildMove(Move):
    def __init__(self, player: Player.Player, btype: Consts.PurchasableType, location: int,
                 free: bool = False):
        super().__init__(player, MoveType.BUILD)
        self.__to_build = btype
        self.__loc = location
        self.__is_free = free

    def is_free(self) -> bool:
        return self.__is_free

    def builds(self) -> Consts.PurchasableType:
        """:returns the building type as a PurchasableType enum"""
        return self.__to_build

    def at(self) -> int:
        """:returns int value of node / edge idx of location to build on the board (see HexGrid)"""
        return self.__loc

    def info(self) -> str:
        return f'[MOVE] player = {self.player()}, ' \
               f'type = {self.get_type().name}, builds = {self.builds().name}, at = {hex(self.at())}'
