import GameSession as GameSession
import GameConstants as Consts
from enum import Enum
import Moves as Moves
import Player as Player
from typing import List, Callable
from random import choice
from Heuristics import *
from copy import deepcopy

import tensorflow as tf
from keras.models import Sequential
from keras.layers import Dense
from DQN import get_move_predictions

class AgentType(Enum):
    RANDOM = 0
    HUMAN = 1
    ONE_MOVE = 2
    PROBABILITY = 3
    EXPROB = 4
    DQN = 5
    OPTIMIZED = 6

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
        inpt = input('Player {}, choose move by index (or n = nodes map, e = edges map, b = board, m = moves list):\n{}\n'.format(player, '\n'.join('{:3} - {}'.format(i, m.info()) for i, m in enumerate(moves))))
        while True:
            if inpt == 'n':
                print(state.board().nodes_map())
                # idx = int(input('Player {}, choose move by index (or -1 for nodes map, -2 for edges map):\n'))
            elif inpt == 'e':
                print(state.board().edges_map())
                # idx = int(input('Player {}, choose move by index (or -1 for nodes map, -2 for edges map):\n'))
            elif inpt == 'b':
                print(state.board())
            elif inpt == 'm':
                print(*(m.info() for m in moves), sep='\n')
            else:
                try:
                    idx = int(inpt)
                    if not 0 <= idx < len(moves):
                        print('supply an integer int the range [0, {}] please'.format(len(moves) - 1))
                    else:
                        move = moves[idx]
                        return move
                except:
                    print('supply an integer int the range [0, {}] please'.format(len(moves) - 1))
            inpt = input(
                'Player {}, choose move by index (or n = nodes map, e = edges map, b = board, m = moves list):\n'.format(
                    player))

    def __repr__(self):
        return self.__name

class OneMoveHeuristicAgent(Agent):
    # Open the tree only one move forward and apply the given heuristic on it
    def __init__(self, heuristic=heuristic_comb1):
        super().__init__(AgentType.ONE_MOVE)
        self.__heur_func = heuristic
        self.__randy = RandomAgent()

    def choose(self, moves: List[Moves.Move], player: Player, state: GameSession) -> Moves.Move:
        hval = 0
        move_values = []
        for move in moves:
            # print(move.info())
            # new_state = state.simulate_move(move)
            new_state = deepcopy(state)
            legal_moves = new_state.simulate_game(move)
            # This is not good enough - simulate move will only choose one random outcome
            # when several are possible (like rolling the dice or buying dev card)
            curr_p = move.player()
            for p in new_state.players():
                if p == move.player():
                    curr_p = p
            hval = self.__heur_func(new_state, curr_p)
            # print('H =', hval)
            move_values.append(hval)
            del new_state

        max_val = max(move_values)
        argmax_vals_indices = [i for i, val in enumerate(move_values) if val == max_val]
        # print(*(f'{move_values[i]} {m.info()}' for i, m in enumerate(moves)), sep='\n')
        moves = [moves[i] for i in argmax_vals_indices]
        move = self.__randy.choose(moves, player, state)
        # print('\n' + move.info() + '\n')
        return move


class ProbabilityAgent(Agent):
    def __init__(self):
        super().__init__(AgentType.PROBABILITY)
        self.__harry = OneMoveHeuristicAgent(probability_score_heuristic)

    def choose(self, moves: List[Moves.Move], player: Player, state: GameSession) -> Moves.Move:
        return self.__harry.choose(moves, player, state)

class OptimizedHeuristicAgent(Agent):
    # using the one move heuristic method
    def __init__(self, heuristic=heuristic_comb1):
        super().__init__(AgentType.OPTIMIZED)
        self.__heur_func = heuristic
        self.__randy = RandomAgent()

    def choose(self, moves: List[Moves.Move], player: Player, state: GameSession) -> Moves.Move:
        h_val = 0
        move_values = []
        for move in moves:
            # improve choice of monopoly dev card before simulating new state:
            if move.get_type() == Moves.MoveType.USE_DEV:
                if move.uses() == Consts.DevType.MONOPOLY:
                    h_val += self.optimize_monopoly_choice(state, player, deepcopy(move))
                    print(h_val)
            # print(move.info())
            new_state = deepcopy(state)
            new_state.simulate_game(move)
            curr_p = move.player()
            for p in new_state.players():
                if p == move.player():
                    curr_p = p

            h_val = self.__heur_func(new_state, curr_p)
            # improve trading abilities:
            if move.get_type() == Moves.MoveType.TRADE:
                h_val += self.optimized_trading_choice(new_state, curr_p, deepcopy(move))/2

            move_values.append(h_val)
            del new_state

        max_val = max(move_values)
        argmax_vals_indices = [i for i, val in enumerate(move_values) if val == max_val]
        moves = [moves[i] for i in argmax_vals_indices]
        move = self.__randy.choose(moves, player, state)
        return move

    def optimize_monopoly_choice(self,session: GameSession, player: Player, move: Moves):
        """
        finds the most common resource among all other players and calculates
        if it is the best choice for the player, considering the player's hand

        :return:
        """
        p = find_sim_player(session, player)
        score = 0
        all_res_from_players = Hand.Hand()
        # all resources from all players:
        [all_res_from_players.insert(other_player.resource_hand()) for other_player in session.players() if other_player != p]
        res_values_all_players = \
            all_res_from_players.map_resources_by_quantity()
        res_values_curr_player = p.resource_hand().map_resources_by_quantity()

        for res_type in res_values_all_players:
            res_values_all_players[res_type] -= res_values_curr_player[
                                                    res_type] / 2
        # for res_type in res_values_all_players:
        #     if p.resource_hand()
        most_common_res = max(res_values_all_players,
                              key=res_values_all_players.get)
        # print("move res: ",move.resource(),"most common: ",most_common_res,
        # "all: ",res_values_all_players)
        if move.resource() == most_common_res:
            score += 0.5
        return score

    def optimized_trading_choice(self,session: GameSession, player: Player,
                              move: Moves):
        """
        prefer trading resources for resources you can't get from dice
        :return:
        """
        p = find_sim_player(session, player)
        res_hand = p.resource_hand()
        score = 0
        if move.get_type() == Moves.MoveType.TRADE:
            __board = session.board()
            res_types_from_dice = __board.resources_player_can_get(player)
            gets_type = move.gets().get_cards_types().pop()
            num_instances_gets_type = res_hand.get_num_instances_of_type(
                gets_type)

            # if what you get from trading you can't achieve from dice:
            if gets_type not in res_types_from_dice:
                # raise score:
                score += 1 / (2 * num_instances_gets_type)
        return score



class ExpectimaxProbAgent(Agent):
    def __init__(self, heuristic: Callable, depth: int = 0, iters: int = 1):
        super().__init__(AgentType.EXPROB)
        self.__depth = depth
        self.__iterations = iters
        self.__h = heuristic
        self.__harry = OneMoveHeuristicAgent(heuristic)
        self.__randy = RandomAgent()
        self.__curr_depth = 2

    def choose(self, moves: List[Moves.Move], player: Player, state: GameSession) -> Moves.Move:
        for p in state.players():
            if p == player:
                player = p
                break
        # max_val = -INF
        # max_moves = [moves[0]]
        # # print('got moves')
        # for m in moves:
        #     new_state = deepcopy(state)
        #     new_state.simulate_game(m)
        #     m_val = self.__h(new_state, player)
        #     # print(m_val, m.info())
        #     del new_state
        #     if m_val > max_val:
        #         max_val = m_val
        #         max_moves = [m]
        #     elif m_val == max_val:
        #         max_moves.append(m)
        # if len(max_moves) == 1:
        #     return max_moves[0]

        # print(f'\nmax moves (val {max_val})')
        # print(*(m.info() for m in max_moves), sep='\n')
        self.__curr_depth -= 1
        max_moves = moves
        all_move_values = []
        move_expected_vals = []
        # num_moves = len(max_moves)
        # print('\nsimulating...')
        for move_idx, move in enumerate(max_moves):
            all_move_values.append([])
            for _i in range(self.__iterations):
                # print(f'i {_i} / {self.__iterations}')
                move_state = deepcopy(state)
                move_state.simulate_game(move)
                self.sim_me(move_state, player)
                for _d in range(self.__depth):
                    # print(f'd {_d} / {self.__depth}')
                    self.sim_me(move_state, player)
                    self.sim_opps(move_state, player)
                value_reached = self.__h(move_state, player)
                # print('H =', value_reached)
                all_move_values[move_idx].append(value_reached)
                del move_state
            avg_move_val = sum(all_move_values[move_idx]) / self.__iterations
            move_expected_vals.append(avg_move_val)
            # print(f'm {move.info()} {move_idx} / {num_moves} --> {avg_move_val}')

        # print(len(all_move_values), len(max_moves))

        # move_expected_vals = [sum(move_vals) / len(move_vals) for move_vals in all_move_values]
        max_val = max(move_expected_vals)
        best_moves = []
        for m_i, m in enumerate(max_moves):
            if move_expected_vals[m_i] == max_val:
                best_moves.append(m)
        # print(f'\nbest moves (exp {max_val})')
        # print(*(m.info() for m in best_moves), sep='\n')
        self.__curr_depth += 1
        if len(best_moves) == 1:
            return best_moves[0]
        else:
            return self.__harry.choose(best_moves, player, state)

    def sim_me(self, session, my_player):
        # possible_moves = session.possible_moves_this_phase()
        # if session.current_player() == my_player and possible_moves:
        #     if self.__curr_depth <= 0:
        #         session.simulate_game(self.__harry.choose(possible_moves, my_player, session))
        #     else:
        #         session.simulate_game(self.choose(possible_moves, my_player, session))

        while session.current_player() == my_player and session.possible_moves():
            session.simulate_game(self.__harry.choose(session.possible_moves(),
                                                      session.current_player(),
                                                      session))

    def sim_opps(self, session, my_player):
        while session.current_player() != my_player and session.possible_moves():
            move_played = self.__randy.choose(session.possible_moves(),
                                              session.current_player(),
                                              session)
            session.simulate_game(move_played)

class DQNAgent(Agent):
    network = tf.keras.models.load_model("current_model")

    def __init__(self):
        super().__init__(AgentType.DQN)

    def choose(self, moves: List[Moves.Move], player: Player, state: GameSession) -> Moves.Move:
        move_preds = get_move_predictions(DQNAgent.network, moves, state)
        chosen_move_index = move_preds[:, 0].argmax()
        return moves[chosen_move_index]
