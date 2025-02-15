import GameSession
from typing import List
from random import sample
import Player
import Agent
import Heuristics
import argparse

DEFAULT_NUM_PLAYERS = 4
RANDOM_AGENT = 'random'
ONE_MOVE_AGENT = 'onemove'
HUMAN_AGENT = 'human'
PROBABILITY_AGENT = 'prob'
MONTECARLO_AGENT = 'monte'
GENETIC_AGENT = 'genetic'
GENETIC_WEIGHTS = (0.77197979,
                   0.8782323,
                   0.07241402,
                   0.82772027,
                   0.45152069,
                   0.17718227,
                   0.37266962,
                   0.15663299,
                   0.19536229)
AGENTS = {
    RANDOM_AGENT: Agent.RandomAgent(),
    ONE_MOVE_AGENT: Agent.OneMoveHeuristicAgent(Heuristics.AmossComb1()),
    HUMAN_AGENT: Agent.HumanAgent(),
    PROBABILITY_AGENT: Agent.ProbabilityAgent(),
    MONTECARLO_AGENT: Agent.MonteCarloAgent(Heuristics.Everything()),
    GENETIC_AGENT: Agent.MonteCarloAgent(Heuristics.Everything(weights=GENETIC_WEIGHTS))
}
DEFAULT_AGENTS = [RANDOM_AGENT]
PLAYER_NAMES = ['Roy', 'Boaz', 'Oriane', 'Amoss']


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-log',
        metavar="LOG_NAME",
        help='The name of the log file - if not specified, no log file will be generated.'
    )
    parser.add_argument(
        '-agents',
        metavar="AGENT",
        nargs='+',
        choices=list(AGENTS.keys()),
        default=DEFAULT_AGENTS,
        help='Agents to use in the game (if # agents does not match # players, last agent will be re-used as necessary)'
    )
    parser.add_argument(
        '-num_players',
        type=int,
        default=DEFAULT_NUM_PLAYERS,
        help='Number of players to play this round of Catan'
    )
    return parser.parse_args()


def init_players(num_players: int, *agent_types: str) -> List[Player.Player]:
    players = []
    p_names = sample(PLAYER_NAMES, num_players)

    for p_idx in range(num_players):
        agent_type = agent_types[p_idx] if p_idx < len(agent_types) else agent_types[-1]
        agent = AGENTS[agent_type]
        players.append(Player.Player(agent, name=p_names[p_idx]))

    return players


def main(log: str = None, num_players: int = DEFAULT_NUM_PLAYERS, agents: List[str] = DEFAULT_AGENTS,
         **kwargs) -> None:
    players = init_players(num_players, *agents)
    catan_session = GameSession.GameSession(log, *players)
    catan_session.run_game()


if __name__ == '__main__':
    args = get_args()
    main(**vars(args))
