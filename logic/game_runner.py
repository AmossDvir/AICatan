from player import *
from game_state import *
from board import *

class GameRunner:
    def __init__(self,player1,player2,player3,player4,board,game_state):
        self.__player1 = player1
        self.__player2 = player2
        self.__player3 = player3
        self.__player4 = player4
        self.__board = board
        self.__game_state = game_state

    def buy_dev_card_for_player(self,player):
        if not player.check_enough_resources(Cost.DEVCARD.value):
            raise ValueError("Not Enough Resources")
        else:
            try:
                print()
                player.buy_dev_card(self.__game_state.withdraw_dev_card())
                print(game_state.get_dev_cards())
            except: print("No More Development Cards")

    def get_player_stats(self,player):
        return str(player)

    def run_game(self):
        pass


if __name__ == '__main__':
    board = CatanBoard()
    p1 = Player(1)
    p2 = Player(2)
    p3 = Player(3)
    p4 = Player(4)
    p1.add_resources([3,5, 40, 40, 40])
    game_state = GameState(p1,p2,p3,p4,board)
    game = GameRunner(p1,p2,p3,p4,board,game_state)
    print(game.get_player_stats(p1))
    game.buy_dev_card_for_player(p1)


    for i in range(29):
        game.buy_dev_card_for_player(p1)
    print(game.get_player_stats(p1))
    # for i in range(14):
    #     p1.play_dev_card(DevCardsTypes.KNIGHT)
    # print(game.get_player_stats(p1))
    #
