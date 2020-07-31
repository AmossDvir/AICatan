import random as rnd
import argparse
<<<<<<< HEAD

from player import Player
from game_state import GameState
from board import CatanBoard
=======
>>>>>>> e76e2c3bf4bc683b858f3b1edbea8177a708c465
from agents import agent

class GameRunner:
    def __init__(self, agents):
        self.agents = {} # Dict from player_id to agent
        for i, agent in enumerate(agents):
            self.agents[i + 1] = agent
        self.player_num = len(agents)
        self.__board = CatanBoard()
<<<<<<< HEAD
        self.__game_state = GameState(self.player_num, self.__board)
=======
        self.__game_state = GameState()
>>>>>>> e76e2c3bf4bc683b858f3b1edbea8177a708c465
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
            if turn % (self.player_num + 1) == 0:
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
        PLAYERS_ORDER_SETUP = list(range(1, self.player_num+1)) + list (range(self.player_num, 0, -1))
        if is_setup_phase:
            for i in PLAYERS_ORDER_SETUP:
                action = self.agents[i].play(self.__game_state)
                self.__game_state = self.__game_state.generate_successor(action)
    
        for turn in self.turn_gen():
            while self.__game_state.current_player() == turn:
                # Get actions from the agents as long as it is it's turn
                action = self.agents[i].play(self.__game_state)
                self.__game_state = self.__game_state.generate_successor(action)
                if self.__game_state.is_game_over():
                    self.game_over()

    def game_over(self):
        print(f'\n\nGame has ended!!!')
        print(f'player {self.__game_state.get_winner()} have won!\n\n')
        exit(0)
            

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-a', '--agents',
        help='Agents type', type=str.lower, # This casts the input into lowercase
        metavar="agent", default='random', nargs='+')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = parse_args()
    if len(args.agents) != 3 and len(args.agents) != 4:
        raise ValueError(f'Invalid number of players! got {len(args.agents)} agents.')

    agents = []
    for i, agent_name in enumerate(args.agents):
        # Make a new agent of the given type
        # i+1 is the player id (we start from 1)
        agents.append(agent.make_agent(agent_name, i + 1)) 

    game = GameRunner(agents)
    game.run_game(True)
