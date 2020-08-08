import numpy as np
import hexgrid
import pickle
from copy import deepcopy
from GameConstants import *
from GameSession import *

INPUT_SIZE = 560
# Overall size = 560:
# Cards:
# Agent's resources Hand:         5
# Other players hands:            15
# Agent's (closed) dev card Hand: 5
# Other players hidden dev cards: 3
# Open dev cards (non-Knights):   5
# Open knights (per player):      4
# Board:
# Boolean city/settlemets (54x4): 216
# Boolean roads (72x4):           288
# Boolean Robber                  19

# Notice that we have to change the player's order since they are not symmetrical
# since we have more information about the current player, so regardless of the
# players numbering, the current player is always the first

def session_to_input(session):
    # Basuc setup:
    edges = list(hexgrid.legal_edge_coords()) # So we can get the indices
    nodes = list(hexgrid.legal_node_coords()) # same
    current_player = session.current_player()
    other_players = []
    for p in session.players():
        if p is not current_player:
            other_players.append(p)
    hand_data = np.zeros(37, np.uint8)

    # Resources Hand:
    for i, player in enumerate([current_player] + other_players):
        for j, resc in enumerate(YIELDING_RESOURCES):
            hand_data[i*5 + j] = len(player.resource_hand().cards_of_type(resc))
    # Agent's (closed) dev card Hand: 5
    for i, dev in enumerate([DevType.KNIGHT, DevType.VP, DevType.MONOPOLY, DevType.YEAR_OF_PLENTY, DevType.ROAD_BUILDING]):
        hand_data[20+i] = len(current_player.dev_hand().cards_of_type(dev))
    # Other players hidden dev cards: 3
    for i, p in enumerate(other_players):
        hand_data[25+i] = len(p.dev_hand())
    # used dev cards:   5
    used = deepcopy(current_player.used_dev_hand())
    for p in other_players:
        used.insert(p.used_dev_hand())
    for i, dev in enumerate([DevType.KNIGHT, DevType.VP, DevType.MONOPOLY, DevType.YEAR_OF_PLENTY, DevType.ROAD_BUILDING]):
        hand_data[28+i] = len(used.cards_of_type(dev))
    # Open knights (per player): 4
    for i, p in enumerate([current_player] + other_players):
        hand_data[33+i] = len(p.dev_hand().cards_of_type(DevType.KNIGHT))

    # Board:
    board = session.board()
    # Boolean city/settlemets (54x4): 216
    city_sett_data = np.zeros(216, np.uint8)
    for i, p in enumerate([current_player] + other_players):
        for j in p.settlement_nodes():
            index = nodes.index(j)
            city_sett_data[(54 * i) + index] = 1
        for j in p.city_nodes():
            index = nodes.index(j)
            city_sett_data[(54 * i) + index] = 2
    # Boolean roads (72x4):           288
    roads_data = np.zeros(288, np.uint8)
    for i, p in enumerate([current_player] + other_players):
        for j in p.road_edges():
            index = edges.index(j)
            roads_data[(72 * i) + index] = 1
    # Boolean Robber
    robber_data = [i == board.robber_hex().id() - 1 for i in range(19)]
    data = np.hstack([hand_data, city_sett_data, roads_data, robber_data])
    print(data)
    return data

if __name__ == "__main__":
    file = open('log.pkl', 'rb')
    for i in range(100):
        s = pickle.load(file)
    # print(s.status_table())
    session_to_input(s)



