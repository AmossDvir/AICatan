import random

class RandomAgent:
    def __init__(self, player_id):
        self.player_id = player_id

    def play(self, game_state):
        actions = game_state.player_legal_actions(self.player_id)
        return random.choice(actions)