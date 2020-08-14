import GameSession
from typing import List
import random
import Agent
import Player
import Agent
import Heuristics
import argparse

VECTOR_SIZE = 11
GENERATING_CEIL = 3
EPSILON_CHILD = 0.1
EPSILON_IMPROVE = 0.2
MUTATE_DEVIATION = 0.3
GENERATING_DEVIATION = 0.5
ROUND_SIZE = 10

def main():
    vecs = [get_random_vec() for _ in range(4)]
    for _ in range(10):
        wins, vps = play_round(vecs)
        improve(vecs, wins, vps)


def improve(vecs, wins, vps):
    """
    We merge the two best vectors, delete the worst one and mutate the mediocre one
    """
    # Order according to wins, break ties with vps:
    order_vecs = [0, 1, 2, 3].sort(key=lambda i:wins[i]*(max(vps)+1) + vps[i])
    # For readability:
    best_i = order_vecs[-1]
    second_best_i = order_vecs[-2]
    mediocre_i = order_vecs[1]
    worst_i = order_vecs[0]
    vecs[worst_i] = reproduce(vecs[best_i], vps[best_i], vecs[second_best_i], vps[second_best_i])
    if random.random() < EPSILON_IMPROVE:
        mutate(vecs[mediocre_i])
    print(f'The new best vector is {vecs[worst_i]}')


def play_round(vectors):
    """
    Plays one round with the given vectors, return the results
    :param vectors: 4 vectors representing the agents
    :return: tuple (list of number of wins, list of total vps) each list is 4 elements
    """
    wins = [0] * len(vectors)
    vps = [0] * len(vectors)
    agents = [vec_to_agent(vec) for vec in vectors]
    for _ in range(ROUND_SIZE):
        players = [Player.Player(agent) for agent in agents]
        session = GameSession.GameSession(None, *players)
        session.run_game()
        winner = session.winner()
        for i, player in enumerate(players):
            if winner == player:
                wins[i] += 1
            vps[i] += player.vp()
    return wins, vps

def get_random_vec():
    return [random.gauss(1, GENERATING_DEVIATION) for _ in range(VECTOR_SIZE)]

def reproduce(vector1, vp1, vector2, vp2):
    percent1 = vp1 / (vp1 + vp2) # The vector that have more VP gets more genetic material
    percent2 = vp2 / (vp1 + vp2)
    child = [(vector1[i] * percent1) + (vector2[i] * percent2) for i in range(VECTOR_SIZE)]
    if random.random() < EPSILON_CHILD:
        mutate(child)
    return child

def mutate(vector):
    # slightly alter a vector:
    for i in range(VECTOR_SIZE):
        # Each value is sampled from gaussian distribution where the previous value is the mean:
        vector[i] = random.gauss(vector[i], MUTATE_DEVIATION)

def vec_to_agent(vector):
    heur = lambda session, player: Heuristics.linear_heuristic(session, player, vector)
    return Agent.OneMoveHeuristicAgent(heuristic=heur)


if __name__ == "__main__":
    main()