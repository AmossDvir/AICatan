import GameSession
from typing import List
from random import sample
import Agent
import Player
import Agent
import Heuristics
import argparse
import json

DEFAULT_NUM_PLAYERS = 4
RANDOM_AGENT = 'random'
ONE_MOVE_AGENT = 'onemove'
HUMAN_AGENT = 'human'
PROBABILITY_AGENT = 'prob'
EXPROB_AGENT = 'exp'
AGENTS = {
    RANDOM_AGENT: Agent.RandomAgent(),
    ONE_MOVE_AGENT: Agent.OneMoveHeuristicAgent(),
    HUMAN_AGENT: Agent.HumanAgent(),
    PROBABILITY_AGENT: Agent.ProbabilityAgent(),
    EXPROB_AGENT: Agent.MonteCarloAgent(Heuristics.everything_heuristic)
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
    # args = get_args()
    # main(**vars(args))
    # a = Agent.ExpectimaxProbAgent(Heuristics.heuristic_comb1)
    # a2 = Agent.ExpectimaxProbAgent(Heuristics.everything_heuristic)


    # batch 1:
    a = Agent.OptimizedHeuristicAgent()
    a2 = Agent.OneMoveHeuristicAgent()
    batch_size = 50
    batch_results = []
    batch_vp_histories = []
    batch_vp_file_name = 'optiComb1_optiComb1_omhComb1_omhComb1_vp'
    batch_res_file_name = 'optiComb1_optiComb1_omhComb1_omhComb1_res'
    for run in range(batch_size):
        try:
            p1 = Player.Player(a, 'Amoss')
            p2 = Player.Player(a, 'Boaz')
            p3 = Player.Player(a2, 'Oriane')
            p4 = Player.Player(a2, 'Roy')
            session = GameSession.GameSession(None, p1, p2, p3, p4)
            session.run_game()
            vp_hist = session.vp_history()    # {p1: [2,2,2,2,2,22,2,3,3,3,3,3,3,4,,6,4,]}
            results = dict(Oriane=0, Amoss=0, Boaz=0, Roy=0, turns=0) # {'p1': 0, }
            results['Amoss'] = p1.vp()
            results['Boaz'] = p2.vp()
            results['Oriane'] = p3.vp()
            results['Roy'] = p4.vp()
            results['turns'] = session.num_turns_played()
            batch_vp_histories.append(vp_hist)
            batch_results.append(results)
        except Exception as e:
            print(e)

    with open(batch_res_file_name, 'w') as f:
        f.write(json.dumps(batch_results))

    with open(batch_vp_file_name, 'w') as f:
        f.write(json.dumps(batch_vp_histories))


    # batch 2:
    a = Agent.OneMoveHeuristicAgent()
    a2 = Agent.OptimizedHeuristicAgent()
    a3 = Agent.MonteCarloAgent(Heuristics.everything_heuristic)
    a4 = Agent.ProbabilityAgent()
    batch_size = 30
    batch_results = []
    batch_vp_histories = []
    batch_vp_file_name = 'omhComb1_optiComb1_exProbEveHeu_prob_vp'
    batch_res_file_name = 'omhComb1_optiComb1_exProbEveHeu_prob_res'
    for run in range(batch_size):
        try:
            p1 = Player.Player(a, 'Amoss')
            p2 = Player.Player(a2, 'Boaz')
            p3 = Player.Player(a3, 'Oriane')
            p4 = Player.Player(a4, 'Roy')
            session = GameSession.GameSession(None, p1, p2, p3, p4)
            session.run_game()
            vp_hist = session.vp_history()  # {p1: [2,2,2,2,2,22,2,3,3,3,3,3,3,4,,6,4,]}
            results = dict(Oriane=0, Amoss=0, Boaz=0, Roy=0,turns=0)  # {'p1': 0, }
            results['Amoss'] = p1.vp()
            results['Boaz'] = p2.vp()
            results['Oriane'] = p3.vp()
            results['Roy'] = p4.vp()
            results['turns'] = session.num_turns_played()
            batch_vp_histories.append(vp_hist)
            batch_results.append(results)
        except Exception as e:
            print(e)

    with open(batch_res_file_name, 'w') as f:
        f.write(json.dumps(batch_results))

    with open(batch_vp_file_name, 'w') as f:
        f.write(json.dumps(batch_vp_histories))

