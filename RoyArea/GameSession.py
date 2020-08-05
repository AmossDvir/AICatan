from __future__ import annotations
from typing import Generator, Union, List
from itertools import combinations
from copy import deepcopy
import GameConstants as Consts
import Board
import Dice
import Player
import Hand
import Moves
import Buildable
import hexgrid

DEBUG = True

def dprint(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)


class GameSession:
    # def __init__(self, agent1: Agent.Agent, agent2: Agent.Agent, agent3: Agent.Agent, agent4: Agent.Agent = None):
    def __init__(self, *players: Player.Player):
        assert Consts.MIN_PLAYERS <= len(players) <= Consts.MAX_PLAYERS

        # game board & dice #
        self.__board = Board.Board()
        self.__dice = Dice.Dice()

        # players #
        self.__turn_order = self.__init_turn_order(*players)
        self.__num_players = len(self.__turn_order)
        self.__player_colors = ()

        # resources deck #
        self.__res_deck = Hand.Hand(*Consts.RES_DECK)

        # development cards deck #
        self.__dev_deck = Hand.Hand(*Consts.DEV_DECK)

        # misc #
        self.__dev_cards_bought_this_turn = Hand.Hand()
        self.__curr_turn_idx = 0
        self.__num_turns_played = 0

    def run_game(self) -> None:
        self.__run_pre_game()

        for curr_player in self.__turn_generator(self.__num_players):
            self.__dev_cards_bought_this_turn = Hand.Hand()  # to know if player can use a dev card

            # print(self.info())
            # TODO add option to use dev card before roll?

            self.__dice.roll()
            dprint('\n\n' + '*'*100)
            dprint('*' * 45, 'NEXT TURN', '*' * 44)
            dprint('*'*100 + '\n')
            # print(self.info(), '\n')
            dprint(f'[RUN GAME] Rolling dice... {self.__dice.sum()} rolled')
            if self.__dice.sum() == Consts.ROBBER_DICE_VALUE:  # robber activated
                dprint('[RUN GAME] Robber Activated! Checking for oversized hands...')

                # remove cards from oversized hands
                for player in self.players():
                    player_hand_size = player.resource_hand_size()
                    if player_hand_size > Consts.MAX_CARDS_IN_HAND:
                        throw_move = player.choose(self.__get_possible_throw_moves(player, player_hand_size // 2),
                                                   deepcopy(self))
                        cards_thrown = throw_move.throws()
                        dprint(f'[RUN GAME] player {player} had too many cards ({player_hand_size}), '
                               f'he threw {cards_thrown}')
                        player.throw_cards(cards_thrown)
                        self.__res_deck.insert(cards_thrown)

                # move robber
                knight_move = curr_player.choose(
                    self.__get_possible_knight_moves(curr_player, robber=True), deepcopy(self))
                robber_hex = knight_move.hex_id()
                opp = knight_move.take_from()
                self.__robber_protocol(curr_player, robber_hex, opp)

            else:  # not robber
                # distribute resources
                dprint(f'[RUN GAME] distributing resources...')
                dist = self.__board.resource_distributions(self.__dice.sum())
                for player, hand in dist.items():
                    removed = self.__res_deck.remove_as_much(hand)
                    player.receive_cards(removed)
                    dprint(f'[RUN GAME] player {player} received {removed}, '
                           f'now has {player.resource_hand()}')

                # query player for move #
                moves_available = self.get_possible_moves(curr_player)
                dprint(f'[RUN GAME] player {curr_player} can play:\n')
                dprint('\n'.join(m.info() for m in moves_available) + '\n')
                move_to_play = curr_player.choose(moves_available, deepcopy(self))
                dprint(f'[RUN GAME] player {curr_player} is playing: {move_to_play.info()}')
                # if any(m.get_type() == Moves.MoveType.THROW for m in moves_available):
                #     print('MOVES AVAILABLE IS BAD', moves_available)
                #     exit()
                self.__apply_move(move_to_play)

                while move_to_play.get_type() != Moves.MoveType.PASS:
                    moves_available = self.get_possible_moves(curr_player)
                    dprint(f'[RUN GAME] player {curr_player} can play:\n')
                    dprint('\n'.join(m.info() for m in moves_available) + '\n')
                    move_to_play = curr_player.choose(moves_available, deepcopy(self))
                    dprint(f'[RUN GAME] player {curr_player} is playing: {move_to_play.info()}')
                    # if any(m.get_type() == Moves.MoveType.THROW for m in moves_available):
                    #     print('MOVES AVAILABLE IS BAD', moves_available)
                    #     exit()
                    self.__apply_move(move_to_play)

            dprint(self.board())
            if self.__is_game_over():
                dprint(f'\n\n\nGAME OVER - player {curr_player} won!!!')
                break

    def current_player(self) -> Player.Player:
        return self.players()[self.curr_turn()]

    def curr_turn(self) -> int:
        return self.__curr_turn_idx

    def players(self) -> List[Player.Player]:
        return self.__turn_order

    def board(self) -> Board.Board:
        return self.__board

    def largest_army_player(self) -> Union[Player.Player, None]:
        player = max(self.players(), key=lambda x: x.army_size())
        if self.largest_army_size() >= Consts.MIN_LARGEST_ARMY_SIZE:
            return player

    def largest_army_size(self) -> int:
        return max(p.army_size() for p in self.players())

    def longest_road_player(self) -> Union[Player.Player, None]:
        player = max(self.players(), key=lambda x: x.longest_road_length())
        if self.longest_road_length() >= Consts.MIN_LONGEST_ROAD_SIZE:
            return player

    def longest_road_length(self) -> int:
        return max(p.longest_road_length() for p in self.players())

    def get_possible_moves(self, player: Player.Player) -> List[Moves.Move]:
        moves = []

        ### PASS TURN ###
        moves.append(Moves.Move(player, Moves.MoveType.PASS))

        ### BUY ###
        # Buy Dev Move Legality
        if (self.__can_purchase(player, Consts.PurchasableType.DEV_CARD) and
                self.__dev_deck.size() > 0):
            moves.append(Moves.BuyDevMove(player))

        ### USE ###
        # Use Dev Card Legality
        for dev_type in Consts.DevType:     # get dev card type
            if player.dev_hand().contains(Hand.Hand(dev_type)):   # if has it
                # if wasnt bought this turn or had at least 1 more from before this turn
                if (dev_type not in self.__dev_cards_bought_this_turn or
                        player.dev_hand().cards_of_type(dev_type).size() >
                        self.__dev_cards_bought_this_turn.cards_of_type(dev_type).size()):
                    if dev_type == Consts.DevType.MONOPOLY:
                        for resource in Consts.YIELDING_RESOURCES:
                            moves.append(Moves.UseMonopolyDevMove(player, resource))
                    elif dev_type == Consts.DevType.YEAR_OF_PLENTY:
                        for resource_comb in combinations(Consts.YIELDING_RESOURCES, Consts.YOP_NUM_RESOURCES):
                            moves.append(Moves.UseYopDevMove(player, *resource_comb))
                    elif dev_type == Consts.DevType.ROAD_BUILDING:
                        moves.append(Moves.UseRoadBuildingDevMove(player))
                    elif dev_type == Consts.DevType.KNIGHT:
                        robber_hex = self.board().robber_hex()
                        for hex_tile in self.board().hexes():
                            if hex_tile is not robber_hex and hex_tile.resource() != Consts.ResourceType.DESERT:
                                opponents_on_hex = set()
                                for node in hex_tile.nodes():
                                    if self.board().nodes().get(node) is not None:  # TODO board.node_occupied() ?
                                        opp = self.board().nodes().get(node).player()
                                        if opp != player:
                                            opponents_on_hex.add(opp)
                                if opponents_on_hex:
                                    for opp in opponents_on_hex:
                                        moves.append(Moves.UseKnightDevMove(player, hex_tile.id(), opp))
                                else:
                                    moves.append(Moves.UseKnightDevMove(player, hex_tile.id(), None))

                    elif dev_type == Consts.DevType.VP:
                        moves.append(Moves.UseDevMove(player, dev_type))

        ### BUILD ###
        # Build settlement legality
        if (self.__can_purchase(player, Consts.PurchasableType.SETTLEMENT) and
                self.__has_remaining_settlements(player)):
            # print('CAN BUY SETTLEMENT, BUILDABLE NODES:')
            for node in self.__buildable_nodes(player):
                # print(node)
                moves.append(Moves.BuildMove(player, Consts.PurchasableType.SETTLEMENT, node))

        # build city legality
        if (self.__can_purchase(player, Consts.PurchasableType.CITY) and
                self.__has_remaining_cities(player)):
            # print('CAN BUY CITY, SETTLE NODES:')
            for settlement_node in player.settlement_nodes():
                # print(settlement_node)
                moves.append(Moves.BuildMove(player, Consts.PurchasableType.CITY, settlement_node))

        # build road legality
        if (self.__can_purchase(player, Consts.PurchasableType.ROAD) and
                self.__has_remaining_roads(player)):
            # print('CAN BUY ROAD, BUILDABLE EDGES:')
            for edge_id in self.__buildable_edges(player):
                # print(edge_id)
                moves.append(Moves.BuildMove(player, Consts.PurchasableType.ROAD, edge_id))

        ### TRADE ###
        # trade legality with deck
        for homogeneous_hand in self.__homogeneous_hands_of_size(player, Consts.DECK_TRADE_RATIO):
            for available_resource in self.__available_resources():
                moves.append(Moves.TradeMove(player, homogeneous_hand, Hand.Hand(available_resource)))

        # trade legality with general harbor
        if self.__has_general_harbor(player):
            for homogeneous_hand in self.__homogeneous_hands_of_size(player, Consts.GENERAL_HARBOR_TRADE_RATIO):
                for available_resource in self.__available_resources():
                    moves.append(Moves.TradeMove(player, homogeneous_hand, Hand.Hand(available_resource)))

        # trade legality with resource harbor
        for resource in player.harbor_resources():
            cards_out = Hand.Hand(*[resource for _ in range(Consts.RESOURCE_HARBOR_TRADE_RATIO)])
            if player.resource_hand().contains(cards_out):
                for available_resource in self.__available_resources():
                    moves.append(Moves.TradeMove(player, cards_out, Hand.Hand(available_resource)))

        return moves

    def simulate_move(self, move: Moves.Move) -> GameSession:
        state = deepcopy(self)
        print('***************************************************APPLYING MOCK MOVE', move.info(), 'TO STATE ', state)
        state.__apply_move(move, printout=True, mock=True)
        return state

    def info(self) -> str:
        ret_val = []
        ret_val.append(f'[TURN] turn belongs to player = {self.current_player()}')
        ret_val.append(f'[TURN] total turns played so far = {self.__num_turns_played}')
        ret_val.append(self.__dice.info())
        ret_val.append(f'\n[LARGEST ARMY] player {self.largest_army_player()}')
        ret_val.append(f'[LONGEST ROAD] player {self.longest_road_player()}')
        ret_val.append('[SCORES] {}\n'.format(', '.join(
            f'player {p_id} = {player.vp()}VP' for p_id, player in enumerate(self.players()))))
        for p in self.players():
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
        return '\n'.join(ret_val)

    def __init_turn_order(self, *players: Player.Player) -> List[Player.Player]:
        dprint('[CATAN] Catan game started, players rolling dice to establish turn order')
        rolls = []
        for player in players:
            if player is None:
                continue
            dprint(f'[CATAN] agent {player} rolled {self.__dice.roll()} = {self.__dice.sum()}')
            rolls.append((self.__dice.sum(), player))

        rolls.sort(key=lambda x: x[0], reverse=True)  # from highest sum to lowest
        dprint('[CATAN] turn order will be:\n' + '\n'.join(f'Player.Player {player}' for roll, player in rolls))
        return [player for roll, player in rolls]

    def __restore(self, saved_self: GameSession) -> None:
        self.__board = saved_self.__board
        self.__dice = saved_self.__dice
        self.__turn_order = saved_self.__turn_order
        self.__res_deck = saved_self.__res_deck
        self.__dev_deck = saved_self.__dev_deck
        self.__num_players = saved_self.__num_players

    def __turn_generator(self, num_players: int) -> Generator[Player.Player]:
        while True:
            self.__num_turns_played += 1
            yield self.players()[self.__curr_turn_idx]
            self.__curr_turn_idx = (self.__curr_turn_idx + 1) % num_players

    def __run_pre_game(self) -> None:
        dprint('[CATAN] Pre-Game started')
        for _round in (1, 2):
            turn_gen = ((player for player in self.players())               # 0, 1, 2, 3
                        if _round == 1 else
                        (player for player in reversed(self.players())))    # 3, 2, 1, 0
            for curr_player in turn_gen:
                print(self.board())

                # get player's choice of settlement
                build_settlement_move = curr_player.choose(
                    self.__get_possible_build_settlement_moves(curr_player, pre_game=True), deepcopy(self))
                adj_edges = self.board().get_adj_edges_to_node(build_settlement_move.at())
                possible_road_moves = [Moves.BuildMove(curr_player, Consts.PurchasableType.ROAD, edge)
                                       for edge in adj_edges]

                # get player's choice of road
                build_adj_road_move = curr_player.choose(possible_road_moves, deepcopy(self))
                settlement_node, road_edge = build_settlement_move.at(), build_adj_road_move.at()
                dprint(f'[PRE GAME] player {curr_player} placed settlement at {hex(settlement_node)}, '
                       f'road at {hex(road_edge)}')

                # add new settlement to game
                settlement = Buildable.Buildable(curr_player, settlement_node, Consts.PurchasableType.SETTLEMENT)
                curr_player.add_buildable(settlement)
                self.__board.build(settlement)

                # add new road to game
                road = Buildable.Buildable(curr_player, road_edge, Consts.PurchasableType.ROAD)
                curr_player.add_buildable(road)
                self.__board.build(road)

                if _round == 2:  # second round, yield resources from settlement
                    starting_resources = self.__board.resource_distributions_by_node(settlement_node)
                    self.__res_deck.remove(starting_resources)
                    curr_player.receive_cards(starting_resources)
                    dprint(f'[PRE GAME] player {curr_player} received {starting_resources} '
                           f'for his 2nd settlement at {hex(settlement_node)}')
        print(self.board())

    def __is_game_over(self) -> bool:
        return any(player.vp() >= Consts.WINNING_VP for player in self.players())

    def __robber_protocol(self, curr_player: Player.Player, robber_hex_id: int, opp: Player.Player,
                          printout=True, mock=False) -> None:
        self.__board.move_robber_to(robber_hex_id)
        if printout:
            dprint(f'[ROBBER PROTOCOL] player {curr_player} placed robber at hex id {robber_hex_id}')

        # get all players adj to hex with robber
        possible_players = set()
        for node in hexgrid.nodes_touching_tile(robber_hex_id + 1):
            if node in self.__board.nodes():
                opp = self.__board.nodes().get(node).player()
                if opp != curr_player:
                    possible_players.add(opp)

        if printout:
            dprint(f'[ROBBER PROTOCOL] opponent players adjacent to hex: {possible_players}')

        # choose victim
        if opp is not None:

            if printout:
                dprint(f'[ROBBER PROTOCOL] stealing from player {opp}')

            # take card from player
            opp_hand = opp.resource_hand()
            if opp_hand.size():
                removed_card = Consts.ResourceType.UNKNOWN if mock else opp_hand.remove_random_card()
                curr_player.receive_cards(removed_card)
                if printout:
                    dprint(f'[ROBBER PROTOCOL] player {curr_player} took {removed_card} from player {opp}')
            elif printout:
                dprint(f'[ROBBER PROTOCOL] player {curr_player} cannot take card from from player {opp}, '
                       f'hand is empty')
        elif printout:
            dprint(f'[ROBBER PROTOCOL] no players adjacent to hex {robber_hex_id}')

    def __apply_move(self, move: Moves.Move, printout=True, mock=False) -> None:
        if move.get_type() == Moves.MoveType.PASS:
            return
        player = move.player()
        saved_state = deepcopy(self)
        try:
            if isinstance(move, Moves.BuyDevMove):
                dev_cost = Consts.COSTS.get(Consts.PurchasableType.DEV_CARD)
                player.throw_cards(dev_cost)
                self.__res_deck.insert(dev_cost)
                card = Hand.Hand(Consts.DevType.UNKNOWN) if mock else self.__dev_deck.remove_random_card()
                player.receive_cards(card)
                self.__dev_cards_bought_this_turn.insert(card)
                if printout:
                    dprint(f'[APPLY MOVE] player {player} bought dev card, got {card}')

            elif isinstance(move, Moves.BuildMove):
                if move.builds() == Consts.PurchasableType.CITY:
                    settlement_node_to_delete = move.at()
                    del self.board().nodes()[settlement_node_to_delete]
                    player.remove_settlement(settlement_node_to_delete)

                buildable_cost = Consts.COSTS.get(move.builds())
                player.throw_cards(buildable_cost)
                self.__res_deck.insert(buildable_cost)

                buildable = Buildable.Buildable(player, move.at(), move.builds())
                player.add_buildable(buildable)
                self.__board.build(buildable)
                if printout:
                    dprint(f'[APPLY MOVE] player {player} built {move.builds()} at {move.at()}')

                # update longest road player
                if buildable.type() == Consts.PurchasableType.ROAD:
                    longest_road_player = self.longest_road_player()
                    for player in self.players():
                        player.set_longest_road(player == longest_road_player)

            elif isinstance(move, Moves.UseDevMove):
                dev_used = move.uses()
                player.use_dev(dev_used)  # remove the card
                if printout:
                    dprint(f'[APPLY MOVE] player {player} used {dev_used} dev card')

                if isinstance(move, Moves.UseKnightDevMove):
                    # update largest army
                    largest_army_player = self.largest_army_player()
                    for player in self.players():
                        player.set_largest_army(player == largest_army_player)

                    hex_id = move.hex_id()
                    opp = move.take_from()
                    self.__robber_protocol(player, hex_id, opp, printout=printout, mock=mock)

                elif isinstance(move, Moves.UseMonopolyDevMove):
                    hand_gained = Hand.Hand()
                    resource_type = move.resource()
                    if printout:
                        dprint(f'[APPLY MOVE] player {player} chose {resource_type} as monopoly resource')

                    for opp in self.players():
                        if opp != player:
                            cards = opp.resource_hand().remove_by_type(resource_type)
                            dprint(f'[APPLY MOVE] opponent {opp} gave {cards}')
                            hand_gained.insert(cards)

                    player.receive_cards(hand_gained)

                    if printout:
                        dprint(f'[APPLY MOVE] player {player} gained {hand_gained.size()} {resource_type}')

                elif isinstance(move, Moves.UseRoadBuildingDevMove):
                    possible_road_moves = self.__get_possible_build_road_moves(player)
                    for _ in range(Consts.ROAD_BUILDING_NUM_ROADS):
                        if not possible_road_moves:
                            break
                        road_move = player.choose(possible_road_moves, deepcopy(self))
                        possible_road_moves.remove(road_move)
                        road = Buildable.Buildable(player, road_move.at(), Consts.PurchasableType.ROAD)
                        self.__board.build(road)
                        player.add_buildable(road)
                        dprint(f'[APPLY MOVE] player {player} built road at {road_move.at()}')

                    # update longest road player
                    longest_road_player = self.longest_road_player()
                    for player in self.players():
                        player.set_longest_road(player == longest_road_player)

                elif isinstance(move, Moves.UseYopDevMove):
                    resources = move.resources()
                    self.__res_deck.remove(resources)
                    player.receive_cards(resources)
                    if printout:
                        dprint(f'[APPLY MOVE] player {player} chose {resources} as YOP resources')

            elif isinstance(move, Moves.TradeMove):
                cards_received = move.gets()
                player.receive_cards(cards_received)
                self.__res_deck.remove(cards_received)

                cards_given = move.gives()
                player.throw_cards(cards_given)
                self.__res_deck.insert(cards_given)

                if printout:
                    dprint(f'[APPLY MOVE] player {player} traded {cards_given} for {cards_received}')

        except ValueError as e:
            dprint(f'player {player} tried to do move {move.get_type().name}, got error: \n{e}')
            if DEBUG:
                exit()
            self.__restore(saved_state)
            del saved_state

    @staticmethod
    def __can_purchase(player: Player.Player, item: Consts.PurchasableType) -> bool:
        players_hand = player.resource_hand()
        item_cost = Consts.COSTS.get(item)
        retval = players_hand.contains(item_cost)
        # print(f'CAN PURCHASE: player {player_id}, player hand {players_hand}, to purchase {item.name} --> {retval}')
        return retval

    @staticmethod
    def __has_remaining_settlements(player: Player.Player) -> bool:
        return player.num_settlements() < Consts.MAX_SETTLEMENTS_PER_PLAYER

    @staticmethod
    def __has_remaining_cities(player: Player.Player) -> bool:
        return player.num_cities() < Consts.MAX_CITIES_PER_PLAYER

    @staticmethod
    def __has_remaining_roads(player: Player.Player) -> bool:
        return player.num_roads() < Consts.MAX_ROADS_PER_PLAYER

    def __buildable_nodes(self, player: Player.Player, pre_game: bool = False) -> List[int]:
        player_nodes = set()
        if pre_game:
            return [node for node in hexgrid.legal_node_coords() if self.__is_distant_node(node)]
        else:
            for edge_id in player.road_edges():
                for node in hexgrid.nodes_touching_edge(edge_id):
                    if self.board().nodes().get(node) is None:
                        player_nodes.add(node)
            # print('NODEs DISTANT:', [hex(node) for node in player_nodes if self.__is_distant_node(node)])
            return [node for node in player_nodes if self.__is_distant_node(node)]

    def __buildable_edges(self, player: Player.Player) -> List[int]:
        player_nodes = set()
        for road_edge in player.road_edges():
            for node in hexgrid.nodes_touching_edge(road_edge):
                player_nodes.add(node)

        adj_edges = set()
        for node in player_nodes:
            for edge_id in self.board().get_adj_edges_to_node(node):
                adj_edges.add(edge_id)

        for existing_edge in player.road_edges():
            if existing_edge in adj_edges:
                adj_edges.remove(existing_edge)

        to_remove = []
        for edge in adj_edges:
            if edge not in hexgrid.legal_edge_coords() or self.board().edges().get(edge) is not None:
                to_remove.append(edge)

        for edge in to_remove:
            adj_edges.remove(edge)

        return list(adj_edges)

    def __is_distant_node(self, node_id: int) -> bool:
        adj_nodes = self.__board.get_adj_nodes_to_node(node_id) + [node_id]
        return all(self.__board.nodes().get(adj) is None for adj in adj_nodes)

    @staticmethod
    def __has_general_harbor(player: Player.Player) -> bool:
        return Consts.ResourceType.ANY in player.harbor_resources()

    @staticmethod
    def __homogeneous_hands_of_size(player: Player.Player, sz: int) -> List[Hand.Hand]:
        hands = []
        players_hand = player.resource_hand()
        for resource in Consts.ResourceType:
            homogeneous_hand = Hand.Hand(*(resource for _ in range(sz)))
            if players_hand.contains(homogeneous_hand):
                hands.append(homogeneous_hand)
        return hands

    def __available_resources(self) -> List[Consts.ResourceType]:
        available = []
        for resource in Consts.ResourceType:
            if self.__res_deck.contains(Hand.Hand(resource)):
                available.append(resource)
        return available

    def __get_possible_knight_moves(self, player: Player.Player, robber: bool = False) -> List[Moves.UseKnightDevMove]:
        moves = []
        dev_type = Consts.DevType.KNIGHT
        if robber or player.dev_hand().contains(Hand.Hand(dev_type)):  # if has it
            # if wasnt bought this turn or had at least 1 more from before this turn
            if robber or (dev_type not in self.__dev_cards_bought_this_turn or
                    player.dev_hand().cards_of_type(dev_type).size() >
                    self.__dev_cards_bought_this_turn.cards_of_type(dev_type).size()):
                robber_hex = self.board().robber_hex()
                for hex_tile in self.board().hexes():   # get hex, cant place at same place or back at desert
                    if hex_tile is not robber_hex and hex_tile.resource() != Consts.ResourceType.DESERT:
                        opponents_on_hex = []        # finding opponents with buildables around hex
                        for node in hex_tile.nodes():   # get node around hex that is occupied
                            if self.board().nodes().get(node) is not None:  # TODO board.node_occupied() ?
                                opp = self.board().nodes().get(node).player()
                                if opp != player and opp not in opponents_on_hex:  # if its not occupied by you...
                                    opponents_on_hex.append(opp)    # then its an opponent
                        if opponents_on_hex:
                            for opp in opponents_on_hex:
                                moves.append(Moves.UseKnightDevMove(player, hex_tile.id(), opp))
                        else:   # no opponents, make move without opp id
                            moves.append(Moves.UseKnightDevMove(player, hex_tile.id(), None))
        # print('KNIGHT MOVES', moves)
        return moves

    @staticmethod
    def __get_possible_throw_moves(player: Player.Player, num_to_throw: int) -> List[Moves.ThrowMove]:
        players_cards = [card for card in player.resource_hand()]
        throw_combinations = list()
        for comb in combinations(players_cards, num_to_throw):
            throw_hand = Hand.Hand(*comb)
            # if throw_hand not in throw_combinations:
            #     throw_combinations.append(throw_hand)
            throw_combinations.append(throw_hand)

        throw_moves = [Moves.ThrowMove(player, hand) for hand in throw_combinations]
        return throw_moves

    def __get_possible_build_road_moves(self, player: Player.Player) -> List[Moves.BuildMove]:
        moves = []
        if self.__has_remaining_roads(player):
            moves = [Moves.BuildMove(player, Consts.PurchasableType.ROAD, edge)
                     for edge in self.__buildable_edges(player)]
        return moves

    def __get_possible_build_settlement_moves(self, player: Player.Player, pre_game: bool = False) -> List[Moves.BuildMove]:
        moves = [Moves.BuildMove(player, Consts.PurchasableType.SETTLEMENT, node)
                 for node in self.__buildable_nodes(player, pre_game)]
        # print('POSSIBLE SETTLE MOVES', moves)
        return moves


if __name__ == '__main__':
    from Agent import RandomAgent

    # a1 = HumanAgent(0, 'kiki')
    # a2 = HumanAgent(1, 'ty')
    # a3 = HumanAgent(2, 'oriane')
    a0 = RandomAgent(0)
    # p1 = RandomAgent(1)
    # p2 = RandomAgent(2)
    p0 = Player.Player(a0)
    p1 = Player.Player(a0)
    p2 = Player.Player(a0)
    p3 = Player.Player(a0)
    g = GameSession(p0, p1, p2, p3)
    g.run_game()
