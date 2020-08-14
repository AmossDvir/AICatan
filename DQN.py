import numpy as np
import tensorflow as tf
import hexgrid
import pickle
from copy import deepcopy

import HexTile
from GameConstants import *
from GameSession import *
from Board import *
from Moves import *
from Dice import PROBABILITIES
from Hand import Hand
from tqdm import tqdm

from keras.models import Sequential
from keras.layers import Dense

BATCH_SIZE = 128
INPUT_SIZE = 698
# Overall size = 698:

# Cards Overall:                  37
# Agent's resources Hand:         5
# Other players hands:            15
# Agent's (closed) dev card Hand: 5
# Other players hidden dev cards: 3
# Open dev cards (non-Knights):   5
# Open knights (per player):      4

# Board Overall:                  637
# Boolean hex_type (19x6):        114
# Boolean city/settlemets (54x4): 216
# Boolean roads (72x4):           288
# Boolean Robber                  19

# Features Overall:               24
# Player vp                       4
# Player access to resource(4*5)  20


# Notice that we have to change the player's order since they are not symmetrical
# since we have more information about the current player, so regardless of the
# players numbering, the current player is always the first

def session_to_input(session):
    all_players = get_player_order(session)
    hand_vec = get_hand_vec(all_players)
    board = session.board()
    board_vec = get_board_vec(board, all_players)
    feature_vec = get_feature_vec(board, all_players)
    data = np.hstack([hand_vec, board_vec, feature_vec])
    return data

def get_hand_vec(players):
    hand_data = np.zeros(37, np.uint8)
    # Resources Hand:
    for i, player in enumerate(players):
        for j, resc in enumerate(YIELDING_RESOURCES):
            hand_data[i*5 + j] = len(player.resource_hand().cards_of_type(resc))
    # Agent's (closed) dev card Hand: 5
    for i, dev in enumerate([DevType.KNIGHT, DevType.VP, DevType.MONOPOLY, DevType.YEAR_OF_PLENTY, DevType.ROAD_BUILDING]):
        hand_data[20+i] = len(players[0].dev_hand().cards_of_type(dev))
    # Other players hidden dev cards: 3
    for i, p in enumerate(players[1:]):
        hand_data[25+i] = len(p.dev_hand())
    # used dev cards:   5
    used = deepcopy(players[0].used_dev_hand())
    for p in players[1:]:
        used.insert(p.used_dev_hand())
    for i, dev in enumerate([DevType.KNIGHT, DevType.VP, DevType.MONOPOLY, DevType.YEAR_OF_PLENTY, DevType.ROAD_BUILDING]):
        hand_data[28+i] = len(used.cards_of_type(dev))
    # Open knights (per player): 4
    for i, p in enumerate(players):
        hand_data[33+i] = len(p.dev_hand().cards_of_type(DevType.KNIGHT))
    return hand_data

def get_board_vec(board, players):
    edges = list(hexgrid.legal_edge_coords()) # So we can get the indices
    nodes = list(hexgrid.legal_node_coords()) # same
    # Tiles
    tile_data = np.zeros(114)
    for i, tile_type in enumerate([ResourceType.FOREST, ResourceType.ORE, ResourceType.BRICK, ResourceType.SHEEP, ResourceType.WHEAT, ResourceType.DESERT]):
        tile_data[i*19:(i+1)*19] = [i.resource() == tile_type for i in board.hexes()]
    # Cities and settlements
    city_sett_data = np.zeros(216, np.uint8)
    for i, p in enumerate(players):
        for j in p.settlement_nodes():
            index = nodes.index(j)
            city_sett_data[(54 * i) + index] = 1
        for j in p.city_nodes():
            index = nodes.index(j)
            city_sett_data[(54 * i) + index] = 2
    # Boolean roads (72x4):           288
    roads_data = np.zeros(288, np.uint8)
    for i, p in enumerate(players):
        for j in p.road_edges():
            index = edges.index(j)
            roads_data[(72 * i) + index] = 1
    # Boolean Robber
    robber_data = [i == board.robber_hex().id() - 1 for i in range(19)]
    return np.hstack([tile_data, city_sett_data, roads_data, robber_data])

def get_feature_vec(board, players):
    token_dict = {i: PROBABILITIES[i]*36 for i in PROBABILITIES}
    res_types = [ResourceType.FOREST, ResourceType.ORE, ResourceType.BRICK, ResourceType.SHEEP, ResourceType.WHEAT]
    hexes = board.hexes()
    feature_data = np.zeros(24)
    feature_data[:4] = [player.vp() for player in players]
    for i, player in enumerate(players):
        for node in player.settlement_nodes():
            tiles = board.get_adj_tile_ids_to_node(node)
            for tile in tiles:
                hexnode = hexes[tile]
                if hexnode.resource() in res_types:
                    feature_data[i*5 + res_types.index(hexnode.resource())] = token_dict[hexnode.token()]
    return feature_data


def make_model():
    model = Sequential()
    model.add(Dense(1000, input_shape=(INPUT_SIZE,), activation='relu'))
    model.add(Dense(1000, activation='relu'))
    model.add(Dense(4, activation='sigmoid'))
    model.compile(loss='mse', metrics=['accuracy'])
    return model

def predict(model, session_batch):
    """
    :param model: The keras model we are are training
    :param session_batch: A list of BATCH_SIZE sessions
    :return: A (BATCH_SIZE, 4) np array of the predicted values
    """
    predicted = np.zeros((len(session_batch), 4))
    for i, session in enumerate(session_batch):        
        legal_moves = session.get_possible_moves(session.current_player())
        move_preds = get_move_predictions(model, legal_moves, session)

        chosen_move_index = move_preds[:, 0].argmax()
        predicted[i, :] = move_preds[chosen_move_index, :]
    return predicted

def get_move_predictions(model, legal_moves, session):
    """
    Returns a np array of shape (len(moves), 4)
    """
    sessions, prob_dict = open_prediction_tree(legal_moves, session)
    inputs = np.zeros((len(sessions), INPUT_SIZE))
    win_status = np.zeros(len(sessions))
    for j, sess in enumerate(sessions):
        inputs[j,:] = session_to_input(sess)
        win_status[j] = get_win_status(sess)
    sess_preds = model.predict(inputs)
    fix_rewards(sess_preds, win_status)
    
    # Calculating according to the expanded tree:
    move_preds = np.zeros((len(legal_moves), 4))
    for j, move in enumerate(prob_dict):
        for sess_index in prob_dict[move]:
            # print('\n\n')
            # print(f'i is is {i}, move is {move}, sess_index is {sess_index}')
            # print(f'sess_preds shape is {sess_preds.shape}')
            # print(f'prob_dict is {prob_dict}')
            move_preds[j,:] += prob_dict[move][sess_index] * sess_preds[sess_index,:]
    return move_preds

def open_prediction_tree(moves, originel_session):
    """
    returns a tuple:
    session list,
    dict from moves to dicts, each from index number of a session to probability
    """
    sessions = []
    move_dict = {}
    for move in moves:
        # The nondeterministic moves are the most complicated
        if move.get_type() == MoveType.BUY_DEV:
            dev_dict = {}
            percent_dict = get_dev_percents(originel_session)
            for dev_type in percent_dict:
                # Create a new session where the player have the card:
                new_sess = deepcopy(originel_session)
                get_player_order(new_sess)[0].receive_cards(Hand(dev_type))
                sessions.append(new_sess)
                dev_dict[len(sessions) - 1] = percent_dict[dev_type]
            move_dict[move] = dev_dict
        if isinstance(move, UseKnightDevMove):
            res_dict = {}
            percent_dict = get_knight_percents(move)
            if percent_dict == None:
                sessions.append(deepcopy(originel_session))
                res_dict = {len(sessions) - 1: 1}
            else:
                for res in percent_dict:
                    new_sess = deepcopy(originel_session)
                    get_player_order(new_sess)[0].receive_cards(Hand(res))
                    sessions.append(new_sess)
                    res_dict[len(sessions) - 1] = percent_dict[res]
            move_dict[move] = res_dict
        # pass is a special case - this is a bit awkward, but we just treat it as identical
        # to the current state
        elif move.get_type() == MoveType.PASS:
            sessions.append(deepcopy(originel_session))
            move_dict[move] = {len(sessions) - 1: 1}
        # The deterministic are pretty simple - they have one outcome with weight of 100%
        else:
            sessions.append(originel_session.simulate_move(move))
            move_dict[move] = {len(sessions) - 1: 1}
    return sessions, move_dict

def get_dev_percents(session):
    """
    Returns a dict {percent: dev_card}
    """
    all_cards = deepcopy(DEV_COUNTS)
    players = get_player_order(session)
    # Remove the open cards of all the players
    for player in players:
        for used in player.used_dev_hand():
            all_cards[used] -= 1
    # Remove the closed card of the current player
    for unused in player.dev_hand():
            all_cards[unused] -= 1
    cards_sum = sum(all_cards[i] for i in all_cards)
    ret_dict = {}
    for dev_type in [DevType.KNIGHT, DevType.VP, DevType.MONOPOLY, DevType.YEAR_OF_PLENTY, DevType.ROAD_BUILDING]:
        ret_dict[dev_type] = all_cards[dev_type] / cards_sum
    return ret_dict

def get_knight_percents(knight_move):
    """
    Returns a dict {percent: resource_card} or None if we don't take from any player
    """
    if knight_move.take_from() == None:
        return None
    hand = knight_move.take_from().resource_hand()
    if len(hand) == 0:
        return None
    percents = {}
    for res_type in [ResourceType.FOREST, ResourceType.ORE, ResourceType.BRICK, ResourceType.SHEEP, ResourceType.WHEAT]:
        percents[res_type] = len(hand.cards_of_type(res_type)) / len(hand)
    return percents

def fix_rewards(predicts, win_status):
    """
    Changes the predicted reward of won games to be 1 and lost games to be 0
    """
    for i, status in enumerate(win_status):
        if status != -1:
            predicts[i, :] = 0
            predicts[i, int(status)] = 1

def get_player_order(session):
    """
    Return the player in the turn order, only the current player is always first
    :param session: The GameSession object
    :return: A list of players
    """
    players = [session.current_player()]
    for p in session.players():
        if p is not session.current_player():
            players.append(p)
    return players

def get_win_status(session):
    """
    Returns -1 if the game is not over, otherwise the index of the winning player
    """
    vps = [player.vp() for player in get_player_order(session)]
    if not any(vp >= WINNING_VP for vp in vps):
        return -1
    else:
        return vps.index(max(vps))

def train_batch(model, session_batch):
    if len(session_batch) == 0:
        return
    batch_size = len(session_batch)
    batch = np.zeros((batch_size, INPUT_SIZE))
    for i in range(batch_size):
        batch[i] = session_to_input(session_batch[i])
    pred = predict(model, session_batch)
    model.fit(batch, pred, batch_size=batch_size, verbose=0)


if __name__ == "__main__":
    model = tf.keras.models.load_model("current_model")
    sessions = []
    for i in range(100):
        # print(f'\n\nOpening file log{i}.pkl:\n')
        file = open(f'log{i}.pkl', 'rb')
        # Load the sessions:
        while(True):
            try:
                sessions.append(pickle.load(file))
            except EOFError:
                break
        # model = make_model()
    print(len(sessions))

    for i in tqdm(range(len(sessions) // BATCH_SIZE)):
        import time
        start = time.time()
        train_batch(model, sessions[i * BATCH_SIZE: (i + 1) * BATCH_SIZE])
        print(f'batch {i} took {time.time() - start}')
    # The leftovers (its important since we actually inject rewards only in the last session):
    if len(sessions) % BATCH_SIZE != 0:
        train_batch(model, sessions[(i + 1) * BATCH_SIZE:])
    model.save('current_model')



