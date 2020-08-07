import GameSession as GameSession
import GameConstants as Consts
from enum import Enum
import Moves as Moves
import Player as Player
from typing import List
from random import choice
from Heuristics import *


class AgentType(Enum):
    RANDOM = 0
    HUMAN = 1
    ONE_MOVE = 2

    def __str__(self):
        return self.name


class Agent:
    ID_GEN = 0

    def __init__(self, agent_type: AgentType):
        Agent.ID_GEN += 1
        self.__id = Agent.ID_GEN
        self.__type = agent_type

    def type(self) -> AgentType:
        return self.__type

    def id(self) -> int:
        return self.__id

    def choose(self, moves: List[Moves.Move], player: Player, state: GameSession) -> Moves.Move:
        raise NotImplemented

    def __str__(self):
        return str(self.type())


class RandomAgent(Agent):
    def __init__(self):
        super().__init__(AgentType.RANDOM)

    def choose(self, moves: List[Moves.Move], player: Player, state: GameSession):
        available_move_types = set([m.get_type() for m in moves])
        move_type = choice(list(available_move_types))

        if move_type == Moves.MoveType.PASS:
            if player.resource_hand().size() > Consts.MAX_CARDS_IN_HAND and len(available_move_types) > 1:
                while move_type == Moves.MoveType.PASS:
                    move_type = choice(list(available_move_types))

        filtered_moves = [m for m in moves if m.get_type() == move_type]

        # from build moves choose uniformly from buildables (same reasoning)
        if move_type == Moves.MoveType.BUILD:
            available_build_types = set([m.builds() for m in filtered_moves])
            build_type = choice(list(available_build_types))
            filtered_moves = [m for m in filtered_moves if m.builds() == build_type]
        elif move_type == Moves.MoveType.USE_DEV:   # same for dev cards
            available_dev_types = set([m.uses() for m in filtered_moves])
            dev_type = choice(list(available_dev_types))
            filtered_moves = [m for m in filtered_moves if m.uses() == dev_type]

        return choice(filtered_moves)


class HumanAgent(Agent):
    def __init__(self, name='human'):
        super().__init__(AgentType.HUMAN)
        self.__name = name

    def choose(self, moves: List[Moves.Move], player: Player, state: GameSession) -> Moves.Move:
        idx = int(input('Player {}, choose move by index:\n{}\n'.format(player, '\n'.join('{:3} - {}'.format(i, m.info()) for i, m in enumerate(moves)))))
        return moves[idx]

    def __repr__(self):
        return self.__name


class OneMoveHeuristicAgent(Agent):
    # Open the tree only one move forward and apply the given heuristic on it
    def __init__(self, heuristic=vp_heuristic):
        super().__init__(AgentType.ONE_MOVE)
        self.__heur_func = heuristic

    def choose(self, moves: List[Moves.Move], player: Player, state: GameSession) -> Moves.Move:
        # print(f"\n\nDEBUG:\n{[move.info() for move in moves]}\n\n")
        move_values = []
        for move in moves:
            new_state = state.simulate_move(move)
            # This is not good enough - simulate move will only choose one random outcome
            # when several are possible (like rolling the dice or buying dev card)
            move_values.append(self.__heur_func(new_state, move.player()))
        argmax = move_values.index(max(move_values))
        return moves[argmax]