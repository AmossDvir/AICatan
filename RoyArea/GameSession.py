from __future__ import annotations
from itertools import combinations
from Board import Board
from Dice import Dice
from Agent import *
from Player import Player
from Hand import Hand
import Moves
import GameConstants as Consts
from typing import Generator, Union
from Buildables import Buildable
from copy import deepcopy
import hexgrid

DEBUG = True


def dprint(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)


class GameSession:
    def __init__(self, agent1: Agent, agent2: Agent, agent3: Agent, agent4: Agent = None):
        # game board & dice #
        self.__board = Board()
        self.__dice = Dice()

        # players #
        self.__players = []
        for player_id, agent in enumerate(self.initialize_turn_order(agent1, agent2, agent3, agent4)):
            self.__players.append(Player(player_id, agent))
        self.__num_players = len(self.__players)

        # resources deck #
        self.__res_deck = Hand(*Consts.RES_DECK)

        # development cards deck #
        self.__dev_deck = Hand(*Consts.DEV_DECK)

        # misc #
        self.__dev_cards_bought_this_turn = Hand()
        self.__next_turn = 0
        self.__num_turns_played = 0

    def restore(self, saved_self: GameSession) -> None:
        self.__board = saved_self.__board
        self.__dice = saved_self.__dice
        self.__players = saved_self.__players
        self.__res_deck = saved_self.__res_deck
        self.__dev_deck = saved_self.__dev_deck
        self.__num_players = saved_self.__num_players

    def get_player_from_agent_id(self, agent_id: int) -> Player:
        for player in self.__players:
            if player.agent().id() == agent_id:
                return player

    def initialize_turn_order(self, *agents: Agent) -> Generator[Agent]:
        dprint('[CATAN] Catan game started, players rolling dice to establish turn order')
        rolls = []
        for agent in agents:
            if agent is None:
                continue
            dprint(f'[CATAN] agent {agent} rolled {self.__dice.roll()} = {self.__dice.sum()}')
            rolls.append((self.__dice.sum(), agent))

        rolls.sort(key=lambda x: x[0], reverse=True)  # from highest sum to lowest
        dprint('[CATAN] turn order will be:\n' + '\n'.join(f'Player {i}: {agent}'
                                                           for i, (roll, agent) in enumerate(rolls)))
        return (agent for roll, agent in rolls)

    def turn_generator(self, num_players: int) -> Generator[int]:
        while True:
            self.__num_turns_played += 1
            yield self.__next_turn
            self.__next_turn = (self.__next_turn + 1) % num_players

    @staticmethod
    def pre_game_first_turn_generator(num_players: int) -> Generator[int]:
        for i in range(num_players):  # 0, 1, 2, 3
            yield i

    @staticmethod
    def pre_game_second_turn_generator(num_players: int) -> Generator[int]:
        for i in range(num_players - 1, -1, -1):  # 3, 2, 1, 0
            yield i

    def curr_turn(self) -> int:
        return self.__next_turn - 1

    def players(self) -> List[Player]:
        return self.__players

    def run_pre_game(self) -> None:
        dprint('[CATAN] Pre-Game started')
        for _round in range(2):
            turn_gen = self.pre_game_first_turn_generator(self.__num_players) \
                if _round == 0 else self.pre_game_second_turn_generator(self.__num_players)
            for player_id in turn_gen:
                print(self.__board)
                build_settlement_move = self.__players[player_id].choose(
                    self.__get_possible_build_settlement_moves(player_id, pre_game=True), deepcopy(self))
                adj_edges = self.board().get_adj_edges_to_node(build_settlement_move.at())
                possible_road_moves = [Moves.BuildMove(player_id, Consts.PurchasableType.ROAD, edge)
                                       for edge in adj_edges]

                build_adj_road_move = self.__players[player_id].choose(possible_road_moves, deepcopy(self))
                # settlement_node, road_edge = self.__players[player_id].choose_settlement_and_road(deepcopy(self))
                settlement_node, road_edge = build_settlement_move.at(), build_adj_road_move.at()
                dprint(f'[PRE GAME] player {player_id} placed settlement at {hex(settlement_node)}, '
                       f'road at {hex(road_edge)}')

                settlement = Buildable(player_id, settlement_node, Consts.PurchasableType.SETTLEMENT)
                self.__players[player_id].add_buildable(settlement)
                self.__board.build(settlement)

                road = Buildable(player_id, road_edge, Consts.PurchasableType.ROAD)
                self.__players[player_id].add_buildable(road)
                self.__board.build(road)

                if _round == 1:  # second round, yield resources
                    starting_resources = self.__board.resource_distributions_by_node(settlement_node)
                    self.__res_deck.remove(starting_resources)
                    self.__players[player_id].receive_cards(starting_resources)
                    dprint(f'[PRE GAME] player {player_id} received {starting_resources} '
                           f'for his 2nd settlement at {hex(settlement_node)}')

    def __game_over(self) -> bool:
        return any(player.vp() >= Consts.WINNING_VP for player in self.__players)

    def __robber_protocol(self, curr_player_id: int, robber_hex_id: int, opp_id: int,
                          printout=True, mock=False) -> None:
        # robber_hex_id = self.__players[curr_player_id].choose_robber_hex(deepcopy(self))
        self.__board.move_robber_to(robber_hex_id)
        if printout:
            dprint(f'[ROBBER PROTOCOL] player {curr_player_id} placed robber at hex id {robber_hex_id}')

        # get all players adj to hex with robber
        possible_player_ids = set()
        for node in hexgrid.nodes_touching_tile(robber_hex_id + 1):
            if node in self.__board.nodes():
                p_id = self.__board.nodes().get(node).player_id()
                if p_id != curr_player_id:
                    possible_player_ids.add(p_id)

        if printout:
            dprint(f'[ROBBER PROTOCOL] opponent players adjacent to hex: {possible_player_ids}')

        # choose victim
        if opp_id is not None:
            p_id = opp_id

            if printout:
                dprint(f'[ROBBER PROTOCOL] stealing from player {p_id}')

            # take card from player
            opp_hand = self.__players[p_id].resource_hand()
            if opp_hand.size():
                removed_card = Consts.ResourceType.UNKNOWN if mock else opp_hand.remove_random_card()
                self.__players[curr_player_id].receive_cards(removed_card)
                if printout:
                    dprint(f'[ROBBER PROTOCOL] player {curr_player_id} took {removed_card} from player {p_id}')
            elif printout:
                dprint(f'[ROBBER PROTOCOL] player {curr_player_id} cannot take card from from player {p_id}, '
                       f'hand is empty')
        elif printout:
            dprint(f'[ROBBER PROTOCOL] no players adjacent to hex {robber_hex_id}')

    def player_with_largest_army(self) -> Union[int, None]:
        player_id = max(self.__players, key=lambda x: x.army_size()).get_id()
        if self.largest_army_size() >= Consts.MIN_LARGEST_ARMY_SIZE:
            return player_id

    def largest_army_size(self) -> int:
        return max(p.army_size() for p in self.__players)

    def player_with_longest_road(self) -> Union[int, None]:
        player_id = max(self.__players, key=lambda x: x.longest_road_length()).get_id()
        if self.longest_road_length() >= Consts.MIN_LONGEST_ROAD_SIZE:
            return player_id

    def longest_road_length(self) -> int:
        return max(p.longest_road_length() for p in self.__players)

    def mock_apply_move(self, move: Moves.Move) -> GameSession:
        state = deepcopy(self)
        print('***************************************************APPLYING MOCK MOVE', move.info(), 'TO STATE ', state)
        state._apply_move(move, printout=True, mock=True)
        return state

    def _apply_move(self, move: Moves.Move, printout=True, mock=False) -> None:
        if move.get_type() == Moves.MoveType.PASS:
            return
        player_id = move.player_id()
        saved_state = deepcopy(self)
        try:
            if isinstance(move, Moves.BuyDevMove):
                dev_cost = Consts.COSTS.get(Consts.PurchasableType.DEV_CARD)
                self.__players[player_id].throw_cards(dev_cost)
                self.__res_deck.insert(dev_cost)
                card = Hand(Consts.DevType.UNKNOWN) if mock else self.__dev_deck.remove_random_card()
                self.__players[player_id].receive_cards(card)   # TODO add support for UNKNOWN
                self.__dev_cards_bought_this_turn.insert(card)  # TODO same
                if printout:
                    dprint(f'[APPLY MOVE] player {player_id} bought dev card, got {card}')

            elif isinstance(move, Moves.BuildMove):
                if move.builds() == Consts.PurchasableType.CITY:
                    settlement_node_to_delete = move.at()
                    del self.board().nodes()[settlement_node_to_delete]
                    self.__players[player_id].remove_settlement(settlement_node_to_delete)

                buildable_cost = Consts.COSTS.get(move.builds())
                self.__players[player_id].throw_cards(buildable_cost)
                self.__res_deck.insert(buildable_cost)

                buildable = Buildable(player_id, move.at(), move.builds())
                self.__players[player_id].add_buildable(buildable)
                self.__board.build(buildable)
                if printout:
                    dprint(f'[APPLY MOVE] player {player_id} built {move.builds()} at {move.at()}')

                # update longest road player
                if buildable.type() == Consts.PurchasableType.ROAD:
                    longest_road_player_id = self.player_with_longest_road()
                    for player in self.__players:
                        player.set_longest_road(player.get_id() == longest_road_player_id)

            elif isinstance(move, Moves.UseDevMove):
                dev_used = move.uses()
                self.__players[player_id].use_dev(dev_used)  # remove the card
                if printout:
                    dprint(f'[APPLY MOVE] player {player_id} used {dev_used} dev card')

                if isinstance(move, Moves.UseKnightDevMove):
                    # update largest army
                    largest_army_player_id = self.player_with_largest_army()
                    for player in self.__players:
                        player.set_largest_army(player.get_id() == largest_army_player_id)

                    hex_id = move.hex_id()
                    opp_id = move.take_from()
                    self.__robber_protocol(player_id, hex_id, opp_id, printout=printout, mock=mock)

                elif isinstance(move, Moves.UseMonopolyDevMove):
                    hand_gained = Hand()
                    # resource_type = self.__players[player_id].choose_monopoly_card(deepcopy(self))
                    resource_type = move.resource()
                    if printout:
                        dprint(f'[APPLY MOVE] player {player_id} chose {resource_type} as monopoly resource')

                    for opp_id, opp in enumerate(self.__players):
                        if opp_id != player_id:
                            cards = opp.resource_hand().remove_by_type(resource_type)
                            # dprint(f'opponent player {opp_id} gave {cards}')
                            hand_gained.insert(cards)

                    self.__players[player_id].receive_cards(hand_gained)

                    if printout:
                        dprint(f'[APPLY MOVE] player {player_id} gained {hand_gained.size()} {resource_type}')

                elif isinstance(move, Moves.UseRoadBuildingDevMove):
                    possible_road_moves = self.__get_possible_build_road_moves(player_id)
                    for _ in range(Consts.ROAD_BUILDING_NUM_ROADS):
                        if not possible_road_moves:
                            break
                        road_move = self.__players[player_id].choose(possible_road_moves, deepcopy(self))
                        possible_road_moves.remove(road_move)
                        road = Buildable(player_id, road_move.at(), Consts.PurchasableType.ROAD)
                        self.__board.build(road)
                        self.__players[player_id].add_buildable(road)
                        dprint(f'[APPLY MOVE] player {player_id} built road at {road_move.at()}')

                    # road_coords = move.edges()
                    # for coord in road_coords:
                    #     road = Buildable(player_id, coord, Consts.PurchasableType.ROAD)
                    #     self.__board.build(road)
                    #     self.__players[player_id].add_buildable(road)

                    # if printout:
                    #     dprint(f'[APPLY MOVE] player {player_id} built roads at {road_coords}')

                    # update longest road player
                    longest_road_player_id = self.player_with_longest_road()
                    for player in self.__players:
                        player.set_longest_road(player.get_id() == longest_road_player_id)

                elif isinstance(move, Moves.UseYopDevMove):
                    # resources = self.__players[player_id].choose_yop_resources(deepcopy(self))
                    resources = move.resources()
                    self.__res_deck.remove(resources)
                    self.__players[player_id].receive_cards(resources)
                    if printout:
                        dprint(f'[APPLY MOVE] player {player_id} chose {resources} as YOP resources')

                    # dprint(f'player {player_id} used Year of Plenty and chose resources {resources}')

            elif isinstance(move, Moves.TradeMove):
                cards_received = move.gets()
                self.__players[player_id].receive_cards(cards_received)
                self.__res_deck.remove(cards_received)

                cards_given = move.gives()
                self.__players[player_id].throw_cards(cards_given)
                self.__res_deck.insert(cards_given)

                if printout:
                    dprint(f'[APPLY MOVE] player {player_id} traded {cards_given} for {cards_received}')

        except ValueError as e:
            dprint(f'player {player_id} tried to do move {move.get_type().name}, got error: \n{e}')
            exit()
            self.restore(saved_state)
            del saved_state

    def run_game(self) -> None:
        self.run_pre_game()
        for curr_player_id in self.turn_generator(self.__num_players):
            self.__dev_cards_bought_this_turn = Hand()  # to know if player can use a dev card

            # TODO add option to use dev card before roll?
            self.__dice.roll()
            dprint('\n\n' + '*'*100)
            dprint('*' * 45, 'NEXT TURN', '*' * 44)
            dprint('*'*100 + '\n')
            # dprint(f'It\'s player {curr_player_id}\'s turn, dice rolled {self.__dice.get_last_roll()}')
            print(self.info(), '\n')

            if self.__dice.sum() == Consts.ROBBER_DICE_VALUE:  # robber activated
                dprint('[RUN GAME] Robber Activated! Checking for oversized hands...')
                # remove cards from oversized hands
                for player in self.__players:
                    player_hand_size = player.resource_hand_size()
                    if player_hand_size > Consts.MAX_CARDS_IN_HAND:
                        throw_move = player.choose(self.__get_possible_throw_moves(player.get_id(), player_hand_size // 2),
                                                   deepcopy(self))
                        cards = throw_move.throws()
                        # cards = player.choose_cards_to_throw(deepcopy(self), player_hand_size // 2)
                        dprint(f'[RUN GAME] player {player.get_id()} had too many cards ({player_hand_size}), '
                               f'he threw {cards}')
                        player.throw_cards(cards)
                        self.__res_deck.insert(cards)

                # move robber
                knight_move = self.__players[curr_player_id].choose(
                    self.__get_possible_knight_moves(curr_player_id, robber=True), deepcopy(self))
                robber_hex = knight_move.hex_id()
                opp_id = knight_move.take_from()
                self.__robber_protocol(curr_player_id, robber_hex, opp_id)

            else:  # not robber
                # distribute resources
                dprint(f'[RUN GAME] {self.__dice.sum()} rolled, distributing resources...')
                dist = self.__board.resource_distributions(self.__dice.sum())
                for p_id, hand in dist.items():
                    removed = self.__res_deck.remove_as_much(hand)
                    self.__players[p_id].receive_cards(removed)
                    dprint(f'[RUN GAME] player {p_id} received {removed}, '
                           f'now has {self.__players[p_id].resource_hand()}')

                # query player for move #
                moves_available = self.get_possible_moves(curr_player_id)
                dprint(f'[RUN GAME] player {curr_player_id} can play:\n', '\n'.join(m.info() for m in moves_available))
                move_to_play = self.__players[curr_player_id].choose(moves_available, deepcopy(self))
                dprint(f'[RUN GAME] player {curr_player_id} is playing: {move_to_play.info()}')
                if any(m.get_type() == Moves.MoveType.THROW for m in moves_available):
                    print('MOVES AVAILABLE IS BAD', moves_available)
                    exit()
                self._apply_move(move_to_play)

                while move_to_play.get_type() != Moves.MoveType.PASS:
                    moves_available = self.get_possible_moves(curr_player_id)
                    dprint(f'[RUN GAME] player {curr_player_id} can play:\n',
                           '\n'.join(m.info() for m in moves_available))
                    move_to_play = self.__players[curr_player_id].choose(moves_available, deepcopy(self))
                    dprint(f'[RUN GAME] player {curr_player_id} is playing: {move_to_play.info()}')
                    if any(m.get_type() == Moves.MoveType.THROW for m in moves_available):
                        print('MOVES AVAILABLE IS BAD', moves_available)
                        exit()
                    self._apply_move(move_to_play)

                # moves = self.__players[curr_player_id].play(deepcopy(self))
                #
                # dprint(f'[RUN GAME] player {curr_player_id} is making these moves: {[m.info() for m in moves]}')
                # for move in moves:
                #     dprint(f'[RUN GAME] applying move: {move.info()}')
                #     self._apply_move(move)

            if self.__game_over():
                dprint(f'\n\n\nGAME OVER - player {self.__next_turn} won!!!')
                break

    def __can_purchase(self, player_id: int, item: Consts.PurchasableType,
                       money_aint_a_thing: bool = False) -> bool:
        # if money_aint_a_thing:
        #     print('MONEY AINT A THING')
        #     return True
        players_hand = self.__players[player_id].resource_hand()
        item_cost = Consts.COSTS.get(item)
        retval = players_hand.contains(item_cost)
        # print(f'CAN PURCHASE: player {player_id}, player hand {players_hand}, to purchase {item.name} --> {retval}')
        return retval

    def __has_remaining_settlements(self, player_id: int) -> bool:
        return self.__players[player_id].num_settlements() < Consts.MAX_SETTLEMENTS_PER_PLAYER

    def __has_remaining_cities(self, player_id: int) -> bool:
        return self.__players[player_id].num_cities() < Consts.MAX_CITIES_PER_PLAYER

    def __has_remaining_roads(self, player_id: int) -> bool:
        return self.__players[player_id].num_roads() < Consts.MAX_ROADS_PER_PLAYER

    def __buildable_nodes(self, player_id: int, pre_game: bool = False) -> List[int]:
        player_nodes = set()
        if pre_game:
            return [node for node in hexgrid.legal_node_coords() if self.is_distant(node)]
        else:
            for edge_id in self.__players[player_id].road_edges():
                for node in hexgrid.nodes_touching_edge(edge_id):
                    player_nodes.add(node)

            return [node for node in player_nodes if self.is_distant(node)]

    def __buildable_edges(self, player_id: int) -> List[int]:
        player_nodes = set()
        for road_edge in self.__players[player_id].road_edges():
            for node in hexgrid.nodes_touching_edge(road_edge):
                player_nodes.add(node)

        adj_edges = set()
        for node in player_nodes:
            for edge_id in self.__board.get_adj_edges_to_node(node):
                adj_edges.add(edge_id)

        for existing_edge in self.__players[player_id].road_edges():
            if existing_edge in adj_edges:
                adj_edges.remove(existing_edge)

        to_remove = []
        for edge in adj_edges:
            if edge not in hexgrid.legal_edge_coords():
                to_remove.append(edge)

        for edge in to_remove:
            adj_edges.remove(edge)
        return list(adj_edges)

    def board(self) -> Board:
        return self.__board

    def is_distant(self, node_id: int) -> bool:
        adj_nodes = self.__board.get_adj_nodes_to_node(node_id) + [node_id]
        return all(self.__board.nodes().get(adj) is None for adj in adj_nodes)

    def __has_general_harbor(self, player_id: int) -> bool:
        return Consts.ResourceType.ANY in self.__players[player_id].harbor_resources()

    def __homogeneous_hands_of_size(self, player_id: int, sz: int) -> List[Hand]:
        hands = []
        players_hand = self.__players[player_id].resource_hand()
        for resource in Consts.ResourceType:
            homogeneous_hand = Hand(*(resource for _ in range(sz)))
            if players_hand.contains(homogeneous_hand):
                hands.append(homogeneous_hand)
        return hands

    def __available_resources(self) -> List[Consts.ResourceType]:
        available = []
        for resource in Consts.ResourceType:
            if self.__res_deck.contains(Hand(resource)):
                available.append(resource)
        return available

    def _settlement_legal_check(self, player_id: int, location: int, pre_game: bool) -> None:
        if self.__board.nodes().get(location) is not None:
            raise ValueError(f'player {player_id} cannot build settlement on {location}, not available')

        adj_nodes = self.__board.get_adj_nodes_to_node(location)
        for adj in adj_nodes:
            if self.__board.nodes().get(adj) is not None:
                raise ValueError(f'player {player_id} cannot build settlement on {location}, adjacent '
                                 f'nodes not empty')
        if not pre_game:
            adj_edges = self.__board.get_adj_edges_to_node(location)
            for adj in adj_edges:
                if self.__board.nodes().get(adj) is not None and self.__board.nodes().get(adj).player_id() == player_id:
                    break
            else:  # no adj road belonging to player found
                raise ValueError(f'player {player_id} cannot build settlement on {location}, no connecting road')

    def __get_possible_knight_moves(self, player_id: int, robber: bool = False) -> List[Moves.UseKnightDevMove]:
        moves = []
        dev_type = Consts.DevType.KNIGHT
        if robber or self.__players[player_id].dev_hand().contains(Hand(dev_type)):  # if has it
            # if wasnt bought this turn or had at least 1 more from before this turn
            if robber or (dev_type not in self.__dev_cards_bought_this_turn or
                    self.__players[player_id].dev_hand().cards_of_type(dev_type).size() >
                    self.__dev_cards_bought_this_turn.cards_of_type(dev_type).size()):
                robber_hex = self.board().robber_hex()
                for hex_tile in self.board().hexes():   # get hex, cant place at same place or back at desert
                    if hex_tile is not robber_hex and hex_tile.resource() != Consts.ResourceType.DESERT:
                        opponents_on_hex = set()        # finding opponents with buildables around hex
                        for node in hex_tile.nodes():   # get node around hex that is occupied
                            if self.board().nodes().get(node) is not None:  # TODO board.node_occupied() ?
                                opp_id = self.board().nodes().get(node).player_id()
                                if opp_id != player_id:  # if its not occupied by you...
                                    opponents_on_hex.add(opp_id)    # then its an opponent
                        if opponents_on_hex:
                            for opp_id in opponents_on_hex:
                                moves.append(Moves.UseKnightDevMove(player_id, hex_tile.id(), opp_id))
                        else:   # no opponents, make move without opp id
                            moves.append(Moves.UseKnightDevMove(player_id, hex_tile.id(), None))
        print('KNIGHT MOVES', moves)
        return moves

    def __get_possible_throw_moves(self, player_id: int, num_to_throw: int) -> List[Moves.ThrowMove]:
        players_cards = [card for card in self.__players[player_id].resource_hand()]
        throw_combinations = list()
        for comb in combinations(players_cards, num_to_throw):
            throw_hand = Hand(*comb)
            # if throw_hand not in throw_combinations:
            #     throw_combinations.append(throw_hand)
            throw_combinations.append(throw_hand)

        throw_moves = [Moves.ThrowMove(player_id, hand) for hand in throw_combinations]
        return throw_moves

    def __get_possible_build_road_moves(self, player_id: int) -> List[Moves.BuildMove]:
        moves = []
        if self.__has_remaining_roads(player_id):
            moves = [Moves.BuildMove(player_id, Consts.PurchasableType.ROAD, edge)
                     for edge in self.__buildable_edges(player_id)]
        return moves

    def __get_possible_build_settlement_moves(self, player_id: int, pre_game: bool = False) -> List[Moves.BuildMove]:
        moves = [Moves.BuildMove(player_id, Consts.PurchasableType.SETTLEMENT, node)
                 for node in self.__buildable_nodes(player_id, pre_game)]
        print('POSSIBLE SETTLE MOVES', moves)
        return moves

    def get_possible_moves(self, player_id: int) -> List[Moves.Move]:
        moves = []

        ### PASS TURN ###
        moves.append(Moves.Move(player_id, Moves.MoveType.PASS))

        ### BUY ###
        # Buy Dev Move Legality
        if (self.__can_purchase(player_id, Consts.PurchasableType.DEV_CARD) and
                self.__dev_deck.size() > 0):
            moves.append(Moves.BuyDevMove(player_id))

        ### USE ###
        # Use Dev Card Legality
        for dev_type in Consts.DevType:     # get dev card type
            if self.__players[player_id].dev_hand().contains(Hand(dev_type)):   # if has it
                # if wasnt bought this turn or had at least 1 more from before this turn
                if (dev_type not in self.__dev_cards_bought_this_turn or
                        self.__players[player_id].dev_hand().cards_of_type(dev_type).size() >
                        self.__dev_cards_bought_this_turn.cards_of_type(dev_type).size()):
                    if dev_type == Consts.DevType.MONOPOLY:
                        for resource in Consts.YIELDING_RESOURCES:
                            moves.append(Moves.UseMonopolyDevMove(player_id, resource))
                    elif dev_type == Consts.DevType.YEAR_OF_PLENTY:
                        for resource_comb in combinations(Consts.YIELDING_RESOURCES, Consts.YOP_NUM_RESOURCES):
                            moves.append(Moves.UseYopDevMove(player_id, *resource_comb))
                    elif dev_type == Consts.DevType.ROAD_BUILDING:
                        moves.append(Moves.UseRoadBuildingDevMove(player_id))
                        # for edge_comb in combinations(self.__buildable_edges(player_id), Consts.ROAD_BUILDING_NUM_ROADS):
                        #     moves.append(Moves.UseRoadBuildingDevMove(player_id, *edge_comb))
                    elif dev_type == Consts.DevType.KNIGHT:
                        robber_hex = self.board().robber_hex()
                        for hex_tile in self.board().hexes():
                            if hex_tile is not robber_hex and hex_tile.resource() != Consts.ResourceType.DESERT:
                                opponents_on_hex = set()
                                for node in hex_tile.nodes():
                                    if self.board().nodes().get(node) is not None:  # TODO board.node_occupied() ?
                                        opp_id = self.board().nodes().get(node).player_id()
                                        if opp_id != player_id:
                                            opponents_on_hex.add(opp_id)
                                if opponents_on_hex:
                                    for opp_id in opponents_on_hex:
                                        moves.append(Moves.UseKnightDevMove(player_id, hex_tile.id(), opp_id))
                                else:
                                    moves.append(Moves.UseKnightDevMove(player_id, hex_tile.id(), None))

                    # elif dev_type == Consts.DevType.VP:
                        moves.append(Moves.UseDevMove(player_id, dev_type))

        ### BUILD ###
        # Build settlement legality
        if (self.__can_purchase(player_id, Consts.PurchasableType.SETTLEMENT) and
                self.__has_remaining_settlements(player_id)):
            # print('CAN BUY SETTLEMENT, BUILDABLE NODES:')
            for node in self.__buildable_nodes(player_id):
                # print(node)
                moves.append(Moves.BuildMove(player_id, Consts.PurchasableType.SETTLEMENT, node))

        # build city legality
        if (self.__can_purchase(player_id, Consts.PurchasableType.CITY) and
                self.__has_remaining_cities(player_id)):
            # print('CAN BUY CITY, SETTLE NODES:')
            for settlement_node in self.__players[player_id].settlement_nodes():
                # print(settlement_node)
                moves.append(Moves.BuildMove(player_id, Consts.PurchasableType.CITY, settlement_node))

        # build road legality
        if (self.__can_purchase(player_id, Consts.PurchasableType.ROAD) and
                self.__has_remaining_roads(player_id)):
            # print('CAN BUY ROAD, BUILDABLE EDGES:')
            for edge_id in self.__buildable_edges(player_id):
                # print(edge_id)
                moves.append(Moves.BuildMove(player_id, Consts.PurchasableType.ROAD, edge_id))

        ### TRADE ###
        # trade legality with deck
        for homogeneous_hand in self.__homogeneous_hands_of_size(player_id, Consts.DECK_TRADE_RATIO):
            for available_resource in self.__available_resources():
                moves.append(Moves.TradeMove(player_id, homogeneous_hand, Hand(available_resource)))

        # trade legality with general harbor
        if self.__has_general_harbor(player_id):
            for homogeneous_hand in self.__homogeneous_hands_of_size(player_id, Consts.GENERAL_HARBOR_TRADE_RATIO):
                for available_resource in self.__available_resources():
                    moves.append(Moves.TradeMove(player_id, homogeneous_hand, Hand(available_resource)))

        # trade legality with resource harbor
        for resource in self.__players[player_id].harbor_resources():
            cards_out = Hand(*[resource for _ in range(Consts.RESOURCE_HARBOR_TRADE_RATIO)])
            if self.__players[player_id].resource_hand().contains(cards_out):
                for available_resource in self.__available_resources():
                    moves.append(Moves.TradeMove(player_id, cards_out, Hand(available_resource)))

        return moves

    def info(self) -> str:
        ret_val = []
        ret_val.append(f'[TURN] turn belongs to player_id = {self.__next_turn}')
        ret_val.append(f'[TURN] total turns played so far = {self.__num_turns_played}')
        ret_val.append(self.__dice.info())
        ret_val.append(f'\n[LARGEST ARMY] player {self.player_with_largest_army()}')
        ret_val.append(f'[LONGEST ROAD] player {self.player_with_longest_road()}')
        ret_val.append('[SCORES] {}\n'.format(', '.join(
            f'player {p_id} = {player.vp()}VP' for p_id, player in enumerate(self.players()))))
        for p in self.__players:
            ret_val.append(p.info())
        ret_val.append(self.__board.info())
        ret_val.append(f'\n[DECKS] cards in play\n[RESOURCES DECK] num cards = {self.__res_deck.size()} / {Consts.NUM_RESOURCES}\n' +
                       '\n'.join('[RESOURCES DECK] {} = {} / {}'.format(
                           r.name, self.__res_deck.cards_of_type(r).size(), amount)
                                 for r, amount in Consts.RESOURCE_COUNTS.items()))
        ret_val.append(f'[DEVS DECK] num cards = {self.__dev_deck.size()} / {Consts.NUM_DEVS}\n' +
                       '\n'.join('[DEVS DECK] {} = {} / {}'.format(
                           d.name, self.__dev_deck.cards_of_type(d).size(), amount)
                                 for d, amount in Consts.DEV_COUNTS.items()))
        # ret_val.append(f'[DEVS BOUGHT] {self.__dev_cards_bought_this_turn}')
        # ret_val.append(f'\n[MOVES] possible moves for player {self.__next_turn}:\n' + '\n'.join(m.info() for m in self.get_possible_moves(self.__next_turn)))
        return '\n'.join(ret_val)


if __name__ == '__main__':
    from Agent import RandomAgent

    # a1 = HumanAgent(0, 'kiki')
    # a2 = HumanAgent(1, 'kiki')
    # a3 = HumanAgent(2, 'oriane')
    a1 = RandomAgent(0)
    a2 = RandomAgent(1)
    a3 = RandomAgent(2)
    g = GameSession(a1, a2, a3)
    g.run_game()
