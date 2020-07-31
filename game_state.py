from enums import *
import random as rnd
from player import Player
from action import Action
import copy

class GameState():
    def __init__(self, player_num, board):
        self.__players = {i: Player(i) for i in range(1, player_num+1)}
        self.__board = board
        self.__dev_cards = [14,5,2,2,2]
        self.__player_with_largest_army = None
        self.__current_player = 1
        self.__dice_rolled = False
        self.__is_pre_game_phase = True

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

    def player_with_largest_army(self):
        # store all knights' players:
        __player1_knights = self.__player1.get_used_dev_cards()[DevCardsTypes.KNIGHT.value]
        __player2_knights = self.__player2.get_used_dev_cards()[DevCardsTypes.KNIGHT.value]
        __player3_knights = self.__player3.get_used_dev_cards()[DevCardsTypes.KNIGHT.value]
        __player4_knights = self.__player4.get_used_dev_cards()[DevCardsTypes.KNIGHT.value]
        __players_knights = [__player1_knights,__player2_knights,__player3_knights,__player4_knights]

        # find maximum:
        __max_knights = max(__players_knights)
        if __max_knights < 3:
            return None

        # find how many have __max_knights:
        __num_of_players_with_most = len([i for i in range(len(__players_knights)) if __players_knights[i] == __max_knights])
        # check if there is a tie:
        if __num_of_players_with_most > 1:
            return self.__player_with_largest_army # just return the first one who reached to it
        else:
            self.__player_with_largest_army = self.__map_player_to_num[ max(range(len(__players_knights)), key = lambda index: __players_knights[index]) + 1]

        return self.__player_with_largest_army


    def _player_with_longest_road(self):
        return self.__board.get_player_with_longest_road()

    def player_legal_actions(self, player_id):
        actions = []
        # if not current player return empty
        if player_id is not self.__current_player:
            return actions
        if self.__is_pre_game_phase:
            return self.pre_game_legal_actions(player_id)
        if not self.__dice_rolled:
            return self.preroll_player_legal_actions(player_id)
        else:
            # TRADE
            actions += self.__players[player_id].get_all_legal_trades()
            # BUY_DEV_CARD
            if self.__players[player_id].check_enough_resources(COST.DEVCARD):
                actions += [Action(ActionType.BUY_DEV_CARD, None)]
            # BUILD ROAD
            if self.__players[player_id].check_enough_resources(COST.ROAD):
                legal_edges = self.__board.get_player_legal_road_edges(player_id)
                actions += [Action(ActionType.BUILD_ROAD, edge) for edge in legal_edges]
            # BUILD_SETTLEMENT
            if self.__players[player_id].check_enough_resources(COST.SETTLEMENT):
                legal_nodes = self.__board.get_player_legal_settlement_nodes(player_id)
                actions += [Action(ActionType.BUILD_SETTLEMENT, node) for node in legal_nodes]
            # BUILD_CITY
            if self.__players[player_id].check_enough_resources(COST.CITY):
                legal_nodes = self.__board.get_player_legal_city_nodes(player_id)
                actions += [Action(ActionType.BUILD_CITY, node) for node in legal_nodes]
            # OPEN_DEV_CARD
            legal_devs = self.__players[player_id].get_legal_dev_cards()
            actions += [Action(ActionType.OPEN_DEV_CARD, card) for card in legal_devs]
            # END_TURN
            actions += [Action(ActionType.END_TURN, None)]
            return actions

    def pre_game_legal_actions(self, player_id):
        actions = []
        nodes = self.__board.setup_get_available_settlement_nodes()
        for node in nodes:
            edges = self.__board.get_empty_edges_around_node(node)
            for edge in edges:
                actions.append(Action(ActionType.SETUP_BUILD, (node, edge)))
        return actions

    def preroll_player_legal_actions(self, player_id):
        actions = [Action(ActionType.ROLL_DICE, None)]
        actions += self.__players[player_id].get_preroll_dev_cards()
        return actions

    def generate_successor(self, action):
        succ = copy.deepcopy(self)
        # TODO: Implement a lot
        if action.action_type == ActionType.TRADE:
            pass
        elif action.action_type == ActionType.BUY_DEV_CARD:
            pass
        elif action.action_type == ActionType.BUILD_ROAD:
            pass
        elif action.action_type == ActionType.BUILD_SETTLEMENT:
            pass
        elif action.action_type == ActionType.BUILD_CITY:
            pass
        elif action.action_type == ActionType.OPEN_DEV_CARD:
            pass
        elif action.action_type == ActionType.MOVE_ROBBER:
            pass
        elif action.action_type == ActionType.ROLL_DICE:
            pass
        elif action.action_type == ActionType.END_TURN:
            pass
        elif action.action_type == ActionType.SETUP_BUILD:
            pass
        

if __name__ == '__main__':
    pass
    # game = GameState(1, 2, 3, 4, 2)
    # print(game.roll_dice())

    # print(p1)