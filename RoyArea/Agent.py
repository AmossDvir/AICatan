from GameSession import GameSession
import GameConstants as Consts
from Hand import Hand
import Moves
from Player import Player
from typing import List, Tuple, Set
from random import choice, sample, uniform
import hexgrid


class Agent:

    def __init__(self, agent_id: int):
        self.__id = agent_id

    def id(self) -> int:
        return self.__id

    def choose(self, moves: List[Moves.Move], state: GameSession) -> int:
        raise NotImplemented

    # def play(self, state: GameSession) -> List[Moves.Move]:
    #     """:returns a list of moves to be done in this turn"""
    #     raise NotImplemented
    #
    # def _player(self, state: GameSession) -> Player:
    #
    #
    # def choose_settlement_and_road(self, state: GameSession) -> Tuple[int, int]:
    #     return state.get_player_from_agent_id(self.id())
    #     raise NotImplemented
    #
    # def take_card_from(self, state: GameSession, possible_players: Set[int]) -> int:
    #     raise NotImplemented
    #
    # def choose_cards_to_throw(self, state: GameSession, num_cards: int) -> Hand:
    #     raise NotImplemented
    #
    # def choose_monopoly_card(self, state: GameSession) -> Consts.ResourceType:
    #     raise NotImplemented
    #
    # def choose_road_building(self, state: GameSession, num_roads: int) -> List[int]:
    #     raise NotImplemented
    #
    # def choose_yop_resources(self, state: GameSession) -> Hand:
    #     raise NotImplemented


class RandomAgent(Agent):

    def choose(self, moves: List[Moves.Move], state: GameSession):
        available_move_types = set([m.get_type() for m in moves])
        move_type = choice(list(available_move_types))
        if state.get_player_from_agent_id(self.id()).resource_hand().size() > 10:
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


    # def play(self, state: GameSession) -> List[Moves.Move]:
    #     """:returns a list of moves to be done in this turn"""
    #     player_id = self._player(state).get_id()
    #     moves = []
    #     moves_left = state.get_possible_moves(player_id)
    #
    #     while moves_left:
    #         if uniform(0, 1) > 0.3:     # with prob. 0.7 stop generating more moves
    #             return moves
    #
    #         # first choose uniformly from available move types.
    #         # because some types have many options and happen every time probabilistically (trade)
    #         available_move_types = set([m.get_type() for m in moves_left])
    #         move_type = choice(list(available_move_types))
    #         filtered_moves = [m for m in moves_left if m.get_type() == move_type]
    #
    #         # from build moves choose uniformly from buildables (same reasoning)
    #         if move_type == Moves.MoveType.BUILD:
    #             available_build_types = set([m.builds() for m in filtered_moves])
    #             build_type = choice(list(available_build_types))
    #             filtered_moves = [m for m in filtered_moves if m.builds() == build_type]
    #
    #         # from use devs choose uniformly
    #
    #         # build_moves = [m for m in moves_left if isinstance(m, Moves.BuildMove) and m.builds() != Consts.PurchasableType.ROAD]
    #         # if build_moves:
    #         #     move_picked = choice(build_moves)
    #         # else:
    #         #     move_picked = choice(moves_left)
    #         move_picked = choice(filtered_moves)
    #         moves.append(move_picked)
    #         print('*************************************BEFORE APPLIED MOVE, MOVES LEFT:\n', '\n'.join(m.info() for m in moves_left))
    #         new_state = state.mock_apply_move(move_picked)
    #         del state
    #         state = new_state
    #         moves_left = state.get_possible_moves(player_id)
    #         print('*************************************AFTER APPLIED MOVE, MOVES LEFT:\n', '\n'.join(m.info() for m in moves_left))
    #
    #
    #     return moves
    #
    # def _player(self, state: GameSession) -> Player:
    #     return state.get_player_from_agent_id(self.id())
    #
    # def choose_robber_hex(self, state: GameSession) -> int:
    #     return choice(range(Consts.NUM_HEXES))
    #
    # def choose_settlement_and_road(self, state: GameSession) -> Tuple[int, int]:
    #     settlement_node = choice(list(hexgrid.legal_node_coords()))
    #     while not state.is_distant(settlement_node):
    #         settlement_node = choice(list(hexgrid.legal_node_coords()))
    #
    #     road_edge = choice(state.board().get_adj_edges_to_node(settlement_node))
    #     return settlement_node, road_edge
    #
    # def take_card_from(self, state: GameSession, possible_players: Set[int]) -> int:
    #     return choice(list(possible_players))
    #
    # def choose_cards_to_throw(self, state: GameSession, num_cards: int) -> Hand:
    #     return Hand(*sample([card for card in self._player(state).resource_hand()], num_cards))
    #
    # def choose_monopoly_card(self, state: GameSession) -> Consts.ResourceType:
    #     card = choice(list(Consts.YIELDING_RESOURCES))
    #     return card
    #
    # def choose_road_building(self, state: GameSession, num_roads: int) -> List[int]:
    #     road_moves = [move.at() for move in state.get_possible_moves(
    #                     self._player(state).get_id(), road_building=True)
    #                     if isinstance(move, Moves.BuildMove) and move.builds() == Consts.PurchasableType.ROAD]
    #     sample_size = min(Consts.ROAD_BUILDING_NUM_ROADS, len(road_moves))
    #     return sample(road_moves, sample_size)
    #
    # def choose_yop_resources(self, state: GameSession) -> Hand:
    #     card1, card2 = self.choose_monopoly_card(state), self.choose_monopoly_card(state)
    #     return Hand(card1, card2)


# class HumanAgent(Agent):
#     def __init__(self, agent_id: int, name='human'):
#         super().__init__(agent_id)
#         self.__name = name
#
#     def play(self, state: GameSession) -> List[Moves.Move]:
#         """:returns a list of moves to be done in this turn"""
#         print(self.__name, "you're up!")
#         moves = []
#         try:
#             types = ['buy', 'use', 'build', 'trade']
#             mtype = input('choose move type: {buy, use, build, trade}\n')
#             while mtype not in types:
#                 mtype = input('try again - choose move type: {buy, use, build, trade}\n')
#
#             if mtype == 'buy':
#                 dev_cost = Consts.COSTS[Consts.PurchasableType.DEV_CARD]
#                 if not self._player(state).resource_hand().contains(dev_cost):
#                     print(f'not enough resources to buy dev card, your hand: {self._player(state).resource_hand()}. try again.')
#                     return self.play(state)
#                 else:
#                     moves.append(Moves.BuyDevMove(self._player(state).get_id()))
#                     return moves + self.play(state)
#
#             elif mtype == 'use':
#                 devtypes = ['knight', 'vp', 'yop', 'monopoly', 'roads']
#                 dtype = input(f'choose dev card type from {devtypes}\n')
#                 while dtype not in types:
#                     dtype = input(f'try again - choose dev card type from {devtypes}\n')
#
#                 if dtype == 'knight':
#                     dtype = Consts.DevType.KNIGHT
#                 elif dtype == 'vp':
#                     dtype = Consts.DevType.VP
#                 elif dtype == 'yop':
#                     dtype = Consts.DevType.YEAR_OF_PLENTY
#                 elif dtype == 'monopoly':
#                     dtype = Consts.DevType.MONOPOLY
#                 elif dtype == 'roads':
#                     dtype = Consts.DevType.ROAD_BUILDING
#
#                 moves.append(Moves.UseDevMove(self._player(state).get_id(), dtype))
#                 return moves + self.play(state)
#
#             elif mtype == 'build':
#                 buildables = ['settle', 'city', 'road']
#                 what = input(f'what to build? {buildables}\n')
#                 while what not in buildables:
#                     what = input(f'try again - choose from {buildables}\n')
#                 where = int(input('where to move? (node / edge coordinate)\n'))
#                 if what == 'settle':
#                     what = Consts.PurchasableType.SETTLEMENT
#                 elif what == 'city':
#                     what = Consts.PurchasableType.CITY
#                 else:
#                     what = Consts.PurchasableType.ROAD
#                 moves.append(Moves.BuildMove(self._player(state).get_id(), what, where))
#                 return moves + self.play(state)
#
#             elif mtype == 'trade':
#                 what = ['W(heat)', 'B(rick)', 'F(orest)', 'S(heep)', 'O(re)']
#                 inp = input(f'what to trade? get? choose from {what}, format ex: WWWW B\n')
#                 give, get = inp.split()
#                 if give.startswith('W'):
#                     hand_give = Hand(*[Consts.ResourceType.WHEAT] * len(give))
#                 elif give.startswith('B'):
#                     hand_give = Hand(*[Consts.ResourceType.BRICK] * len(give))
#                 elif give.startswith('F'):
#                     hand_give = Hand(*[Consts.ResourceType.FOREST] * len(give))
#                 elif give.startswith('S'):
#                     hand_give = Hand(*[Consts.ResourceType.SHEEP] * len(give))
#                 else:
#                     hand_give = Hand(*[Consts.ResourceType.ORE] * len(give))
#
#                 if get.startswith('W'):
#                     hand_get = Hand(*[Consts.ResourceType.WHEAT] * len(give))
#                 elif get.startswith('B'):
#                     hand_get = Hand(*[Consts.ResourceType.BRICK] * len(give))
#                 elif get.startswith('F'):
#                     hand_get = Hand(*[Consts.ResourceType.FOREST] * len(give))
#                 elif get.startswith('S'):
#                     hand_get = Hand(*[Consts.ResourceType.SHEEP] * len(give))
#                 else:
#                     hand_get = Hand(*[Consts.ResourceType.ORE] * len(give))
#
#                 moves.append(Moves.TradeMove(self._player(state).get_id(), hand_give, hand_get))
#                 return moves + self.play(state)
#
#         except KeyboardInterrupt:
#             return moves
#
#     def choose_robber_hex(self, state: GameSession) -> int:
#         print(self.__name, "you're up!")
#         return int(input('choose robber hex id (base 10, 0-indexed)\n'))
#
#     def choose_settlement_and_road(self, state: GameSession) -> Tuple[int, int]:
#         print(self.__name, "you're up!")
#         settle = int(input('choose settlement node\n'), 16)
#         road = int(input('choose road edge\n'), 16)
#         return settle, road
#
#     def take_card_from(self, state: GameSession, possible_players: Set[int]) -> int:
#         print(self.__name, "you're up!")
#         return int(input(f'take card from {possible_players}\n'))
#
#     def choose_cards_to_throw(self, state: GameSession, num_cards: int) -> Hand:
#         print(self.__name, "you're up!")
#         print('self', self, 'type', type(self))
#         inp = input(f'your hand is {self._player(state).resource_hand()} choose {num_cards} cards to throw'
#                     f' - format example: WWBO\n')
#         hand = Hand()
#         for c in inp:
#             if c == 'W':
#                 hand.insert(Hand(Consts.ResourceType.WHEAT))
#             elif c == 'B':
#                 hand.insert(Hand(Consts.ResourceType.BRICK))
#             elif c == 'F':
#                 hand.insert(Hand(Consts.ResourceType.FOREST))
#             elif c == 'S':
#                 hand.insert(Hand(Consts.ResourceType.SHEEP))
#             else:
#                 hand.insert(Hand(Consts.ResourceType.ORE))
#         return hand
#
#     def choose_monopoly_card(self, state: GameSession) -> Consts.ResourceType:
#         print(self.__name, "you're up!")
#         c = input('choose monopoly card (W, B, F, S, O)\n')
#         if c == 'W':
#             return Consts.ResourceType.WHEAT
#         elif c == 'B':
#             return Consts.ResourceType.BRICK
#         elif c == 'F':
#             return Consts.ResourceType.FOREST
#         elif c == 'S':
#             return Consts.ResourceType.SHEEP
#         else:
#             return Consts.ResourceType.ORE
#
#     def choose_road_building(self, state: GameSession, num_roads: int) -> List[int]:
#         print(self.__name, "you're up!")
#         loc1 = int(input('choose road edge 1\n'), 16)
#         loc2 = int(input('choose road edge 2\n'), 16)
#         return [loc1, loc2]
#
#     def choose_yop_resources(self, state: GameSession) -> Hand:
#         print(self.__name, "you're up!")
#         inp = input('choose yop resources - ex: WB / FF\n')
#         hand = Hand()
#         for c in inp:
#             if c == 'W':
#                 hand.insert(Hand(Consts.ResourceType.WHEAT))
#             elif c == 'B':
#                 hand.insert(Hand(Consts.ResourceType.BRICK))
#             elif c == 'F':
#                 hand.insert(Hand(Consts.ResourceType.FOREST))
#             elif c == 'S':
#                 hand.insert(Hand(Consts.ResourceType.SHEEP))
#             else:
#                 hand.insert(Hand(Consts.ResourceType.ORE))
#         return hand
#
#     def __str__(self):
#         return self.__name
#
#     def __repr__(self):
#         return self.__name