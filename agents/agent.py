from agents.random_agent import RandomAgent

def make_agent(agent_name):
    if agent_name == 'random':
        return RandomAgent()
    else:
        raise ValueError(f'Unrecognised agent name: {agent_name}')

# Abstract Class, should only be inherited
class Agent:
    def __init__(self):
        raise ValueError('__init__ function not defined!')

    def play(self, game_state):
        raise ValueError('__init__ function not defined!')
