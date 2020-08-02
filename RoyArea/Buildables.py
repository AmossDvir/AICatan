from enum import IntEnum
from Hand import Hand
import GameConstants as Consts


class Buildable:
    def __init__(self, player_id: int, coord: int, btype: Consts.PurchasableType):
        self.__player_id = player_id
        self.__coord = coord
        if btype == Consts.PurchasableType.DEV_CARD:
            raise ValueError('cannot build dev card')
        self.__type = btype

    def player_id(self) -> int:
        return self.__player_id

    def coord(self) -> int:
        return self.__coord

    def cost(self) -> Hand:
        return Consts.COSTS[self.type()]

    def type(self) -> Consts.PurchasableType:
        return self.__type

    def info(self) -> str:
        return f'[{self.type().name}] node_id = {hex(self.coord())}, player_id = {self.player_id()}'

    def __str__(self):
        return f'{self.type()} at {hex(self.coord())} belonging to player {self.player_id()}'
