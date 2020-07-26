from enum import Enum
import operator
from game_state import DevCardsTypes
from game_state import HarbourTypes
from game_state import GameState

class Resources(Enum):
    WOOD = 0
    BRICK = 1
    SHEEP = 2
    WHEAT = 3
    ORE = 4

class BuildingType(Enum):
    ROAD = 0
    SETTLEMENT = 1
    CITY = 2

class Cost(Enum):
    ROAD = [1, 1, 0, 0, 0]
    SETTLEMENT = [1, 1, 1, 1, 0]
    CITY = [0, 0, 0, 2, 3]
    DEVCARD = [0, 0, 1, 1, 1]

class Player():
    NUM_OF_RESOURCES = 5
    def __init__(self, player_num):
        # a dictionary to help calling the functions for building:
        self.__build_func_call = {BuildingType.ROAD: self._build_road,
                                  BuildingType.SETTLEMENT:
                                      self._build_settlement,
                                  BuildingType.CITY: self._build_city}

        # a dictionary to help calling the functions for dev cards:
        self.__dev_func_call = {DevCardsTypes.KNIGHT: self._play_knight,
                                DevCardsTypes.VICTORY_CARD:
                                    self._play_victory_card(),
                                DevCardsTypes.MONOPOLY: self._play_monopoly(),
                                DevCardsTypes.YEAR_OF_PLENTY:
                                    self._play_year_of_plenty,
                                DevCardsTypes.ROAD_BUILDING:
                                    self._play_road_building}

        self.__player_num = player_num

        # initializing objects:
        self.__player_resources = [0, 0, 0, 0, 0]
        self.__player_dev_cards = [0, 0, 0, 0, 0]
        self.__player_used_knights = [0, 0, 0, 0, 0]
        self.__avail_settlements = 5
        self.__avail_cities = 4
        self.__avail_roads = 15
        self.__victory_points = 0
        self.__harbours = [False,False,False,False,False,False]


    def __str__(self):

        title = f"Player number {self.__player_num}:\nResources:\t\t\tDev Cards:\n"
        line1 = f"\tWood: {self.__player_resources[Resources.WOOD.value]}\t\t\t\tKnights: {self.__player_dev_cards[DevCardsTypes.KNIGHT.value]}\n"
        line2 = f"\tBrick: {self.__player_resources[Resources.BRICK.value]}\t\t\tVictory Cards: {self.__player_dev_cards[DevCardsTypes.VICTORY_CARD.value]}\n"
        line3 = f"\tSheep: {self.__player_resources[Resources.SHEEP.value]}\t\t\tMonopoly: {self.__player_dev_cards[DevCardsTypes.MONOPOLY.value]}\n"
        line4 = f"\tWheat: {self.__player_resources[Resources.WHEAT.value]}\t\t\tYear of Plenty: {self.__player_dev_cards[DevCardsTypes.YEAR_OF_PLENTY.value]}\n"
        line5 = f"\tOre: {self.__player_resources[Resources.ORE.value]}\t\t\t\tRoad Building: {self.__player_dev_cards[DevCardsTypes.ROAD_BUILDING.value]}"

        return title + line1 + line2 + line3 + line4 + line5

    # Getters:
    def get_player_resources(self):
        return self.__player_resources

    def get_player_dev_cards(self):
        return self.__player_dev_cards

    def get_avail_settlements(self):
        return self.__avail_settlements

    def get_avail_cities(self):
        return self.__avail_cities

    def get_avail_roads(self):
        return self.__avail_roads

    def get_player_victory_point(self):
        return self.__victory_points

    def add_resources(self, resources):
        """
        adding given resources to the existing player's resources (vector)
        :param resources: List
        :return: None
        """
        self.__player_resources = list(
            map(operator.add, self.__player_resources, resources))

    def subtract_resources(self, resources):
        """
        subtracting given resources from the existing player's resources
        :param resources: List
        :return: None
        """
        self.__player_resources = list(
            map(operator.sub, self.__player_resources, resources))

    def build(self, type):
        """
        calls to the wanted function for building
        :param type: BuildingType object
        :return: None
        """
        self.__build_func_call[type]()

    def _build_road(self):
        # check if enough resources:
        if not all(list(map(operator.ge, self.__player_resources, Cost.ROAD.value))):
            raise ValueError("Not Enough Resources")


        # check if available roads:
        elif self.__avail_roads < 1:
            raise ValueError("No Roads Left")
        else:
            self.subtract_resources(Cost.ROAD.value)
            self.__avail_roads -= 1

    def _build_settlement(self):
        # check if enough resources:
        if not all(list(map(operator.ge, self.__player_resources, Cost.SETTLEMENT.value))):
            raise ValueError("Not Enough Resources")

        # check if available settlements:
        elif self.__avail_settlements < 1:
            raise ValueError("No Settlements Left")
        else:
            self.subtract_resources(Cost.SETTLEMENT.value)
            self.__avail_settlements -= 1

    def _build_city(self):
        # check if enough resources:
        if not all(list(map(operator.ge, self.__player_resources, Cost.CITY.value))):
            raise ValueError("Not Enough Resources")

        # check if available cities:
        elif self.__avail_cities < 1:
            raise ValueError("No Cities Left")
        else:
            self.subtract_resources(Cost.CITY.value)
            self.__avail_cities -= 1

    def buy_dev_card(self,game_state):
        # check if enough resources:
        if not all(list(map(operator.ge, self.__player_resources, Cost.DEVCARD.value))):
            raise ValueError("Not Enough Resources")
        else:
            try:
                self.subtract_resources(Cost.DEVCARD.value)
                __dev_card = GameState.withdraw_dev_card(game_state)
                self.__player_dev_cards[__dev_card.value] += 1
                print(__dev_card)
            except:
                pass


    def play_dev_card(self, type):
        """
        calls to the wanted function for playing dev card
        :param type: DevCardsTypes object
        :return: None
        """
        # check if the desired card exists:
        if self.__player_dev_cards[type.value] < 1:
            raise ValueError(f"Player Doesn't Have {type.name} Development Card")

        else: self.__dev_func_call[type]()

    def _play_knight(self):
        # todo: continue writing
        pass

    def _play_victory_card(self):
        # todo: continue writing
        pass

    def _play_monopoly(self):
        # todo: continue writing
        pass

    def _play_year_of_plenty(self):
        # todo: continue writing
        pass

    def _play_road_building(self):
        # todo: continue writing
        pass

    def update_harbour_ownership(self,harbour_type):
        """
        updates the harbours, if the player has built a settlement on a harbour
        :param harbour_type:
        :return:
        """
        if harbour_type.isinstance(HarbourTypes):
            self.__harbours[harbour_type.value] = True
        else: raise ValueError(f"{harbour_type} Is Not a Valid Harbour Type")

    def generate_possible_trades(self):
        """
        generates a list of all possible hands after tradings
        :return: List
        """
        trade_value = 4
        if self.__harbours[HarbourTypes.GENERAL3.value]:
            trade_value = 3
        return self.possible_trades_helper(0, self.__player_resources, [],trade_value)

    def possible_trades_helper(self,resource,temp_lst,optional_trading_lst,trade_value):
        """
        generates a list of all possible hands after tradings
        :return: List
        """
        if resource >= Player.NUM_OF_RESOURCES-1: # has reached to the end
            return optional_trading_lst
        if all(res < trade_value for res in temp_lst): # no more possible trades
            return optional_trading_lst
        if temp_lst[resource] >= trade_value: # if the resource can be exchanged
            temp_lst2 = temp_lst[:]

            # generates all possible exchanges for the particular resource:
            for index in range(Player.NUM_OF_RESOURCES):
                temp_lst=temp_lst2[:] # remember the original list
                if resource == index: # can't trade for the same resource
                    continue
                temp_lst[resource] -= trade_value
                temp_lst[index] += 1

                # don't include bad trades (append only the useful trades):
                if not all(list(map(operator.ge, self.__player_resources,temp_lst))):
                    optional_trading_lst.append(temp_lst)
            # for every option check again if possible to trade:
            for option in optional_trading_lst:
                optional_trading_lst += self.possible_trades_helper(0, option[:],[],trade_value)
        return self.possible_trades_helper(resource + 1, temp_lst[:],optional_trading_lst, trade_value)


if __name__ == '__main__':

    p = Player(55)
    p.add_resources([3,5, 4, 4, 3])
    # p.build(BuildingType.ROAD)
    # p.subtract_resources([0, 1, 0, 1, 0])
    # print(p)
    # p.build(BuildingType.CITY)
    # p.play_dev_card(DevCardsTypes.MONOPOLY)
    game = GameState(1, 1, 1, 1, 1)
    # for i in range(26):
    #     p.add_resources([1, 1, 1, 1, 1])
    #     p.buy_dev_card(game)
    #     print(p)
    print(p.generate_possible_trades())