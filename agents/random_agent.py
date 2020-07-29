import random

class RandomAgent:
    def __init__(self):
        pass

    def play(self, game_state):
        actions = game_state.get_current_player_legal_actions()
        return random.choice(actions)