from enums import ActionType

# Actions Have two values, action type and action value

class Action:
    def __init__(self, action_type, value):
        self.action_type = action_type
        self.value = value