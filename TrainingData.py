import numpy as np

from GameSession import *
from DQN import *
from tqdm import tqdm

"""
The value iteration algorithm we are using requires us to use max over several outputs.
We started by doing this in every training epoch, but this proved very slow. instead we
decided to pre-process the data, calculating the children of the states beforehand and
saving only the input vectors and chances for every transition.

Full explanation of the network can be found in DQN.py.

Each instance have:
self.x: The vectors representing the base states,
self.expanded: The vectors representing the children of the base states
self.won_expanded: The winning status of the expanded states
self.child_list: The information requires to train the network using the bellman equation:
the i'th element in child list is a list for every legal move of the i'th session in self.x,
inside each there is tuples with transition probabilty to the state and and index number of
the state in self.expanded.
"""

class TrainingData:
    """
    Representing proccessed data. A inatance of this class contains the input vectors for the base_session,
    the input vectors for the children,  and the information required to train the network using the bellman equation.
    """
    def __init__(self, sessions):
        self.x = np.zeros((len(sessions), INPUT_SIZE))
        expanded_sessions = []
        self.child_list = [] # List of lists of lists (i know...), each contains (prob, session_index)
        for i, session in tqdm(enumerate(sessions)):
            self.x[i,:] = session_to_input(session)
            # new_sessions, move_dict = open_prediction_tree(session.get_possible_moves(session.current_player()), session)
            new_sessions, move_dict = open_prediction_tree(session.possible_moves(), session)
            offset = len(expanded_sessions)
            expanded_sessions += new_sessions
            self.child_list.append([[(offset+sess_i, move_dict[m][sess_i]) for sess_i in move_dict[m]] for m in move_dict])
        
        self.expanded = np.zeros((len(expanded_sessions), INPUT_SIZE))
        self.won_expanded = np.zeros((len(expanded_sessions)), dtype=np.int8) # -1 for game not over, otherwise winner ID
        for i, session in tqdm(enumerate(expanded_sessions)):
            self.expanded[i,:] = session_to_input(session)
            self.won_expanded[i] = get_win_status(session)

    def fit(self, model):
        """
        Uses the information in this instance to train the givel model
        """
        predict_expanded = model.predict(self.expanded)
        fix_rewards(predict_expanded, self.won_expanded)
        y = np.zeros((self.x.shape[0], 4))
        for i, child_list in tqdm(enumerate(self.child_list)):
            for children in child_list:
                result = np.zeros(4)
                max_result = np.zeros(4)
                for child in children:
                    result += child[1] * predict_expanded[child[0],:]
                if result[0] > max_result[0]:
                    max_result = result
            y[i,:] = max_result
        model.fit(self.x, y)

if __name__ == "__main__":
    model = tf.keras.models.load_model("current_model")
    sessions = []
    for i in range(5):
        # print(f'\n\nOpening file log{i}.pkl:\n')
        file = open(f'log{i}.pkl', 'rb')
        # Load the sessions:
        while(True):
            try:
                sessions.append(pickle.load(file))
            except EOFError:
                break
        # model = make_model()
    data = TrainingData(sessions)
    file = open(f'data2.pkl', 'wb')
    pickle.dump(data, file)
    data.fit(model)
    model.save('current_model')
