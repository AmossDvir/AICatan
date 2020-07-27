from enum import Enum
import random as rnd
import player


class DevCardsTypes(Enum):
    KNIGHT = 0
    VICTORY_CARD = 1
    MONOPOLY = 2
    YEAR_OF_PLENTY = 3
    ROAD_BUILDING = 4

class HarbourTypes(Enum):
    WOOD = 0
    BRICK = 1
    SHEEP = 2
    WHEAT = 3
    ORE = 4
    GENERAL3 = 5

class Cost(Enum):
    ROAD = [1, 1, 0, 0, 0]
    SETTLEMENT = [1, 1, 1, 1, 0]
    CITY = [0, 0, 0, 2, 3]
    DEVCARD = [0, 0, 1, 1, 1]


class GameState():

    def __init__(self, player1, player2, player3, player4, board):
        self.__player1 = player1
        self.__player2 = player2
        self.__player3 = player3
        self.__player4 = player4
        self.__board = board

        self.__dev_cards = [14,5,2,2,2]
        self.__is_pre_game_phase = True
        self.__robber_location = 0

    def start_game(self):
        self.__is_pre_game_phase = False

    def roll_dice(self):
        """
        Generates an integer number from 2 to 12
        :return: Integer
        """
        dice1 = rnd.randint(1, 6)
        dice2 = rnd.randint(1, 6)
        return dice1 + dice2

    def withdraw_dev_card(self):
        """
        randomly withdraw a development card from the stack
        :param:
        :return:
        """
        # check if dev cards stack is empty:
        if set(self.__dev_cards) == {0}:
            raise ValueError("No More Development Cards")




        else:
            # calculate the weight of each type of card among the stack:
            knights_wght = int(self.__dev_cards[DevCardsTypes.KNIGHT.value] / sum(self.__dev_cards) * 100)
            Victory_card_wght = int(self.__dev_cards[DevCardsTypes.VICTORY_CARD.value] / sum(self.__dev_cards) * 100)
            monopoly_wght = int(self.__dev_cards[DevCardsTypes.MONOPOLY.value] / sum(self.__dev_cards) * 100)
            year_of_plenty_wght = int(self.__dev_cards[DevCardsTypes.YEAR_OF_PLENTY.value] / sum(self.__dev_cards) * 100)
            road_building_wght = int(self.__dev_cards[DevCardsTypes.ROAD_BUILDING.value] / sum(self.__dev_cards) * 100)

            # generate one card from the stack:
            __card = rnd.choices([card for card in DevCardsTypes], weights=(knights_wght, Victory_card_wght, monopoly_wght,year_of_plenty_wght,road_building_wght)).pop()
            self.__dev_cards[__card.value] -= 1
            # print(__card.name)
            # print(self.__dev_cards)
            # print(knights_wght, Victory_card_wght, monopoly_wght,year_of_plenty_wght,road_building_wght)
            # print("------------------")
            return __card
    def get_dev_cards(self):
        return self.__dev_cards

    def move_robber(self,new_location):
            self.__robber_location = new_location

    def get_player_with_most_victory_points(self):
        # todo: continue writing
        pass



    def _player_with_largest_army(self):
        # todo: continue writing
        pass
        # __player1_knights = self.__player1.get_used_dev_cards()[DevCardsTypes.KNIGHT.value]
        # __player2_knights = self.__player2.get_used_dev_cards()[DevCardsTypes.KNIGHT.value]
        # __player3_knights = self.__player3.get_used_dev_cards()[DevCardsTypes.KNIGHT.value]
        # __player4_knights = self.__player4.get_used_dev_cards()[DevCardsTypes.KNIGHT.value]
        #
        # __players_knights = [__player1_knights,__player2_knights,__player3_knights,__player4_knights]
        #
        # # check if there isn't a tie:
        # if len(set(__players_knights)) == len(__players_knights):
        #
        #     __player_with_most = max(range(len(__players_knights)), key = lambda index: __players_knights[index])
        #

    def _player_with_longest_road(self):
        pass


if __name__ == '__main__':

    pass
    # game = GameState(1, 2, 3, 4, 2)
    # print(game.roll_dice())

    # print(p1)
