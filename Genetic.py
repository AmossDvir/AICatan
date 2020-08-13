import GameSession
from typing import List
import random
import Agent
import Player
import Agent
import Heuristics
import argparse

VECTOR_SIZE = 11
EPSILON_CHILD = 0.1
MUTATE_DEVIATION = 0.3
GENERATING_MEAN = 1.5
GENERATING_DEVIATION = 1
ROUND_SIZE = 10

# The dafualt weights now in the heauristic.py file
BASE_VECTOR = [2, 0.8, 0.2, 0.6, 0.7, 2.5, 0.5, 5, 2, 1, 1]
ONE_VECTOR = [0.26, 0.22, 0.1, 0.56, -0.3, 2.78, 0.21, 6.05, 1.72, 1.85, 0.05]
LATEST_VECTOR = [0.35, 0.2, 0.58, 0.75, 0.14, 2.61, 0.44, 5.3, 2.02, 1.28, 1.68]

def main():
    vecs = [BASE_VECTOR.copy() for _ in range(2)] + [ONE_VECTOR.copy() for _ in range(2)]
    for vec in vecs:
        mutate(vec, GENERATING_DEVIATION)
    for _ in range(10):
        print(f'vecs are {vecs}')
        wins, vps = play_round(vecs)
        improve(vecs, wins, vps)


def improve(vecs, wins, vps):
    """
    We merge the two best vectors, delete the worst one and mutate the mediocre one
    """
    # Order according to wins, break ties with vps:
    order_vecs = [0, 1, 2, 3]
    order_vecs.sort(key=lambda i:wins[i]*(max(vps)+1) + vps[i])
    # For readability:
    best_i = order_vecs[-1]
    second_best_i = order_vecs[-2]
    mediocre_i = order_vecs[1]
    worst_i = order_vecs[0]
    vecs[worst_i] = reproduce(vecs[best_i], vps[best_i], vecs[second_best_i], vps[second_best_i])
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
    return [random.gauss(GENERATING_MEAN, GENERATING_DEVIATION) for _ in range(VECTOR_SIZE)]

def reproduce(vector1, vp1, vector2, vp2):
    percent1 = vp1 / (vp1 + vp2) # The vector that have more VP gets more genetic material
    percent2 = vp2 / (vp1 + vp2)
    child = [(vector1[i] * percent1) + (vector2[i] * percent2) for i in range(VECTOR_SIZE)]
    if random.random() < EPSILON_CHILD:
        mutate(child)
    return child

def mutate(vector, deviation=MUTATE_DEVIATION):
    # slightly alter a vector:
    for i in range(VECTOR_SIZE):
        # Each value is sampled from gaussian distribution where the previous value is the mean:
        vector[i] = random.gauss(vector[i], deviation)

def vec_to_agent(vector):
    heur = lambda session, player: Heuristics.linear_heuristic(session, player, vector)
    return Agent.OneMoveHeuristicAgent(heuristic=heur)

def get_latest_heuristic():
    return lambda session, player: Heuristics.linear_heuristic(session, player, LATEST_VECTOR)


if __name__ == "__main__":
    main()