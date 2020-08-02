from enum import IntEnum
from Hand import Hand
import GameConstants as Consts


class MoveType(IntEnum):
    TRADE = 1
    BUY_DEV = 2
    USE_DEV = 3
    BUILD = 4


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
        return '[MOVE]'

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

