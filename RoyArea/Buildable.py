import GameConstants as Consts
from Hand import Hand
import Player


class Buildable:
    def __init__(self, player: Player, coord: int, btype: Consts.PurchasableType):
        self.__player = player
        self.__coord = coord
        if btype == Consts.PurchasableType.DEV_CARD:
            raise ValueError('cannot build dev card')
        self.__type = btype

    def player(self) -> Player:
        return self.__player

    def coord(self) -> int:
        return self.__coord

    def cost(self) -> Hand:
        return Consts.COSTS[self.type()]

    def type(self) -> Consts.PurchasableType:
        return self.__type

    def info(self) -> str:
        return f'[{self.type().name}] node_id = {hex(self.coord())}, player = {self.player()}'

    def __str__(self):
        return f'{self.type()} at {hex(self.coord())} belonging to player {self.player()}'
