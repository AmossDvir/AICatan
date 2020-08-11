import numpy as np
import tensorflow as tf
import hexgrid
import pickle
from copy import deepcopy
from GameConstants import *
from GameSession import *
from Moves import *
from keras.models import Sequential
from keras.layers import Dense

BATCH_SIZE = 64
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
    # Basic setup:
    edges = list(hexgrid.legal_edge_coords()) # So we can get the indices
    nodes = list(hexgrid.legal_node_coords()) # same
    current_player = session.current_player()
    all_players = get_player_order(session)
    hand_data = np.zeros(37, np.uint8)

    # Resources Hand:
    for i, player in enumerate(all_players):
        for j, resc in enumerate(YIELDING_RESOURCES):
            hand_data[i*5 + j] = len(player.resource_hand().cards_of_type(resc))
    # Agent's (closed) dev card Hand: 5
    for i, dev in enumerate([DevType.KNIGHT, DevType.VP, DevType.MONOPOLY, DevType.YEAR_OF_PLENTY, DevType.ROAD_BUILDING]):
        hand_data[20+i] = len(current_player.dev_hand().cards_of_type(dev))
    # Other players hidden dev cards: 3
    for i, p in enumerate(all_players[1:]):
        hand_data[25+i] = len(p.dev_hand())
    # used dev cards:   5
    used = deepcopy(current_player.used_dev_hand())
    for p in all_players[1:]:
        used.insert(p.used_dev_hand())
    for i, dev in enumerate([DevType.KNIGHT, DevType.VP, DevType.MONOPOLY, DevType.YEAR_OF_PLENTY, DevType.ROAD_BUILDING]):
        hand_data[28+i] = len(used.cards_of_type(dev))
    # Open knights (per player): 4
    for i, p in enumerate(all_players):
        hand_data[33+i] = len(p.dev_hand().cards_of_type(DevType.KNIGHT))

    # Board:
    board = session.board()
    # Boolean city/settlemets (54x4): 216
    city_sett_data = np.zeros(216, np.uint8)
    for i, p in enumerate(all_players):
        for j in p.settlement_nodes():
            index = nodes.index(j)
            city_sett_data[(54 * i) + index] = 1
        for j in p.city_nodes():
            index = nodes.index(j)
            city_sett_data[(54 * i) + index] = 2
    # Boolean roads (72x4):           288
    roads_data = np.zeros(288, np.uint8)
    for i, p in enumerate(all_players):
        for j in p.road_edges():
            index = edges.index(j)
            roads_data[(72 * i) + index] = 1
    # Boolean Robber
    robber_data = [i == board.robber_hex().id() - 1 for i in range(19)]
    data = np.hstack([hand_data, city_sett_data, roads_data, robber_data])
    return data

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
    # TODO: Handle PASS, handle non-determinisitic
    predicted = np.zeros((len(session_batch), 4))
    for i, session in enumerate(session_batch):        
        legal_moves = session.get_possible_moves(session.current_player())
        move_preds = np.zeros((len(legal_moves), 4))
        inputs = np.zeros((len(legal_moves), INPUT_SIZE))
        win_status = np.zeros(len(legal_moves))
        for i, move in enumerate(legal_moves):
            new_sess = session.simulate_move(move)
            inputs[i,:] = session_to_input(new_sess)
            win_status[i] = get_win_status(new_sess)
        move_preds = model.predict(inputs)
        fix_rewards(move_preds, win_status)
        chosen_move_index = move_preds[:, 0].argmax()
        predicted[i, :] = move_preds[chosen_move_index, :]
    return predicted

def open_prediction_tree(moves, originel_session):
    """
    returns a tuple:
    session list,
    dict from moves to dicts, each from probability to an index number of a session 
    """
    sessions = []
    move_dict = {}
    for move in moves:
        # The nondeterministic moves are the most complicated
        if move.get_type() == MoveType.BUY_DEV:
            pass
        elif move.get_type() == MoveType.THROW:
            pass
        # pass is a special case - this is a bit awkward, but we just treat it as identical
        # to the current state
        elif move.get_type() == MoveType.PASS:
            pass
        # The deterministic are pretty simple - they have one outcome with weight of 100%
        else:
            pass
    return sessions, move_dict


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
    batch_size = len(session_batch)
    batch = np.zeros((batch_size, INPUT_SIZE))
    for i in range(batch_size):
        batch[i] = session_to_input(sessions[i])
    pred = predict(model, session_batch)
    model.fit(batch, pred, batch_size=batch_size)

if __name__ == "__main__":
    file = open('log.pkl', 'rb')
    sessions = []
    # Load the sessions:
    while(True):
        try:
            sessions.append(pickle.load(file))
        except EOFError:
            break
    # model = make_model()
    model = tf.keras.models.load_model("current_model")
    for i in range(len(sessions) // BATCH_SIZE):
        train_batch(model, sessions[i * BATCH_SIZE: (i + 1) * BATCH_SIZE])
    # The leftovers (its important since we actually inject rewards only in the last session):
    train_batch(model, sessions[(i + 1) * BATCH_SIZE:])
    model.save('current_model')

    



