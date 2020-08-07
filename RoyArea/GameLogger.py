from copy import deepcopy
import pickle

class GameLogger:
    def __init__(self, log_file_name):
        self.log_file = open(log_file_name, 'wb')

    def __deepcopy__(self, memo):
        # We don't want the logger to be copied when we deepcopy the GameSession
        return None

    def write_session(self, session):
        pickle.dump(session, self.log_file)