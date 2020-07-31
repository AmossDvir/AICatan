from player import *
from game_state import *
from board import *
import random as rnd


class GameRunner:
    PLAYERS_ORDER_SETUP = [1,2,3,4,4,3,2,1]
    def __init__(self, player1, player2, player3, player4, board, game_state):
        self.__player1 = player1
        self.__player2 = player2
        self.__player3 = player3
        self.__player4 = player4
        self.__board = board
        self.__game_state = game_state
        self.__dices_rolled = False

    def buy_dev_card_for_player(self, player):
        if not player.check_enough_resources(Cost.DEVCARD.value):
            raise ValueError("Not Enough Resources")
        else:
            try:
                print()
                player.buy_dev_card(self.__game_state.withdraw_dev_card())
            except:
                print("No More Development Cards")


    def get_player_stats(self, player):
        return str(player)

    def turn_gen(self):
        """
        generates the player id by it's turn
        :return: Iterable Object
        """
        turn = 1
        while True:
            if turn%5 == 0:
                turn = 1
            yield turn
            turn += 1

    def run_game(self,is_setup_phase=False):
        """
        The main function of the game,
        runs the game by the sequence of the players' turns
        :param is_setup_phase: Boolean: determine if it is the initial part
        :return: None
        """
        if is_setup_phase:
            for turn_setup in GameRunner.PLAYERS_ORDER_SETUP:
                node = self.randomly_choose(tuple(self.__board.setup_get_available_settlement_nodes()))
                edge = self.randomly_choose(self.__board.get_empty_edges_around_node(node))
                self.__board.setup_place_settlement_and_road(turn_setup,node,edge)
        else:
            for turn in self.turn_gen():
                dices = self.__game_state.roll_dice()

    def randomly_choose(self,choices_lst):
        """
        ****only for the meanwhile until we create smarter funcs****
        :param choices_lst: List
        :return: Object
        """
        return rnd.choice(choices_lst)

if __name__ == '__main__':
    board = CatanBoard()
    p1 = Player(1)
    p2 = Player(2)
    p3 = Player(3)
    p4 = Player(4)

    game_state = GameState(p1, p2, p3, p4, board)
    game = GameRunner(p1, p2, p3, p4, board, game_state)
    # for turn1 in game.turn_gen():
    #     print(turn1)
    game.run_game(True)
